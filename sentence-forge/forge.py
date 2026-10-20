#!/usr/bin/env python3
"""sentence-forge: find the highest-leverage sentence - or a whole monologue -
you can build from a strictly limited vocabulary, without an LLM.

"Leverage" means everyday usefulness: a sentence earns it by covering the
common situations of daily conversation and by standing on its own, without
needing context. Emotional force is deliberately not rewarded.

Pipeline (all classical):
  1. Vocabulary  - the top-N words of a frequency list ("word count" per line).
  2. Fluency     - interpolated Kneser-Ney trigram LM trained on Tatoeba French,
                   plus hard filters: attested 2/3/4-grams, hashed 5-grams,
                   attested sentence endings.
  3. Coherence   - every pair of content words must co-occur in corpus
                   sentences with positive PMI.
  4. Situations  - ~30k everyday corpus sentences are embedded (SIF over
                   fastText vectors, first principal component removed) and
                   clustered with spherical k-means; each cluster is a common
                   situation, weighted by its share of the corpus.
  5. Leverage    - weighted coverage of those situations, minus penalties for
                   negation, for pronouns that need an antecedent, and for
                   drama: projection on a SemAxis intensity axis (terrible -
                   correct, guerre - discussion, mort - fatigue...), which
                   flags film-style violence and tragedy.
  6. Search      - candidates are real corpus sentences that already fit the
                   vocabulary plus new ones from a diverse beam search; all
                   are re-ranked by leverage.
  7. Discourse   - from film/TV subtitles (real everyday speech) a
                   sentence-ordering model in the style of Lapata (2003)
                   learns PMI between features of a sentence and features of
                   the next one *said by the same speaker* (sentences in one
                   subtitle segment, no dash between them): content words,
                   first word, speech act, person. Subtitle frequency also
                   tells how often a line is said.
  8. Monologue   - a second beam search chains candidates so that each line
                   is a likely continuation of the previous one and stays on
                   the monologue's topic; at most a third negated, and a
                   per-sentence cost sets the length.

Usage:
  python forge.py fetch                         # download data into ./data (~200 MB)
  python forge.py search                        # top-100 words
  python forge.py situations                    # show the situation clusters
  python forge.py monologue
  python forge.py monologue -n 1000 --theme "voyage"
"""
import argparse
import bz2
import gzip
import hashlib
import math
import pickle
import re
import shutil
import sys
import textwrap
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

FREQ_URL = "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/fr/fr_50k.txt"
VEC_URL = "https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.fr.300.vec.gz"
CORPUS_URL = "https://downloads.tatoeba.org/exports/per_language/fra/fra_sentences.tsv.bz2"
SUBS_URL = "https://object.pouta.csc.fi/OPUS-OpenSubtitles/v2018/mono/fr.txt.gz"

BOS, UNK, PAUSE = "<s>", "<unk>", "<p>"
ENDS = {"</.>": ".", "</!>": " !", "</?>": " ?"}

# Finite and infinitive verb forms likely to appear in a small French core
# vocabulary; used only for the optional "must contain a verb" constraint.
VERBS = set("""est a ai suis fait va était as sais veux dit es sont peux avez vais
ont faire être dire été sommes êtes avons allez vont peut sait veut fais vas
avait étais avais aller voir vu sera serait""".split())

# Closed-class words: ignored by the coherence check, which is about how
# content words combine.
FUNCTION_WORDS = set("""de d' je j' est pas le la l' les que qu' vous tu un une c' ce
cette ces à et il ils elle elles on a ai as ont avez avons ne n' en y ça cela
pour des du au aux qui quoi mais dans nous me m' te t' se s' si moi toi lui
leur leurs mon ma mes ton ta tes son sa ses votre vos notre nos sur avec par
ou où comme quand comment pourquoi est-ce suis es sommes êtes sont été être
était étais avait avais sera serait plus très aussi bien non oui alors là ici
tout tous toute toutes rien jamais juste bon merci y a-t-il eu chez sans sous
vers entre après avant pendant depuis encore déjà toujours même autre autres
quelque quelqu' chaque peu trop beaucoup assez fait faire dit dire va vais vas
peux peut veux veut sais sait ,""".split())

# A sentence opening with one of these (or containing est-ce) is a question.
QUESTION_OPENERS = {"pourquoi", "comment", "où", "quoi", "quand", "est-ce", "qu'"}

# A subject pronoun and its own stressed form in one generated sentence is
# almost always wrong ("Tu ne peux pas partir avec toi").
SELF_CLASH = [({"je", "j'"}, "moi"), ({"tu"}, "toi"), ({"il"}, "lui")]

NEGATION = {"ne", "n'", "pas", "jamais", "rien", "personne", "aucun", "aucune"}
# Third-person pronouns point back to something said earlier; a sentence that
# depends on them is useful in fewer situations.
ANAPHORA = {"il", "elle", "ils", "elles", "lui", "leur", "eux"}
# Drama axis (SemAxis-style): mean of (dramatic - everyday) difference
# vectors, each pair sharing a part of speech. Used only as a penalty.
DRAMA_PAIRS = [
    ("toujours", "parfois"), ("jamais", "rarement"), ("absolument", "plutôt"),
    ("terrible", "correct"), ("énorme", "moyen"), ("éternel", "temporaire"),
    ("extraordinaire", "ordinaire"), ("passion", "habitude"), ("guerre", "discussion"),
    ("terreur", "gêne"), ("mort", "fatigue"), ("tuer", "aider"), ("détruire", "modifier"),
    ("sang", "eau"), ("arme", "outil"), ("crime", "erreur"),
]
DRAMA_REFERENCE = 5000      # word scores are z-scored against this many common words

# Rude or vulgar words: common in film dialogue, but no everyday leverage.
RUDE = set("""fous fout foutre foutu merde putain con conne connard connards salaud
salope bordel chier gueule cul crétin idiot idiote imbécile abruti enfoiré
dégage tais-toi ta-gueule pute bâtard emmerde baiser""".split())
REQUEST = {"veux", "voudrais", "peux", "pouvez", "peut", "besoin", "faut",
           "aimerais", "voulez", "puis"}

LETTERS = "a-zàâäçéèêëîïôöùûüÿœæ"
TOKEN_RE = re.compile(rf"[{LETTERS}]+'|[{LETTERS}]+(?:-[{LETTERS}]+)*|[.!?]+|[,;:…«»()\"—–]")


def is_negated(toks):
    return bool(NEGATION & set(toks))


def speech_act(toks, end):
    if end == "</?>":
        return "question"
    if is_negated(toks):
        return "negation"
    if REQUEST & set(toks):
        return "request"
    return "statement"


# ---------------------------------------------------------------- data ----

def download(url, dest):
    print(f"  {url}\n  -> {dest}", file=sys.stderr)
    with urllib.request.urlopen(url) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)


def fetch(args):
    DATA.mkdir(exist_ok=True)
    freq = DATA / "fr_50k.txt"
    if not freq.exists():
        download(FREQ_URL, freq)
    corpus = DATA / "fra_sentences.tsv"
    if not corpus.exists():
        tmp = DATA / "fra_sentences.tsv.bz2"
        download(CORPUS_URL, tmp)
        with bz2.open(tmp, "rb") as src, open(corpus, "wb") as dst:
            shutil.copyfileobj(src, dst)
        tmp.unlink()
    vec = DATA / f"cc.fr.300.top{args.vectors_top // 1000}k.vec"
    if not vec.exists():
        # fastText .vec files are sorted by frequency, so streaming the head
        # of the 1.2 GB archive is enough to cover a small vocabulary.
        print(f"  streaming first {args.vectors_top} vectors of {VEC_URL}", file=sys.stderr)
        with urllib.request.urlopen(VEC_URL) as r, gzip.GzipFile(fileobj=r) as gz, open(vec, "wb") as f:
            for i, line in enumerate(gz):
                f.write(line)
                if i >= args.vectors_top:
                    break
    subs = DATA / f"opensubtitles.fr.{args.subs_lines}.txt"
    if not subs.exists():
        # Subtitles keep each film's lines in order, so the head of the 1 GB
        # archive is a large sample of real, consecutive everyday dialogue.
        print(f"  streaming first {args.subs_lines:,} lines of {SUBS_URL}", file=sys.stderr)
        with urllib.request.urlopen(SUBS_URL) as r, gzip.GzipFile(fileobj=r) as gz, open(subs, "wb") as f:
            for i, line in enumerate(gz):
                if i >= args.subs_lines:
                    break
                f.write(line)
    print("data ready in", DATA, file=sys.stderr)


def load_freq(path, n):
    """Return (top-n words, probability of every listed word)."""
    counts = {}
    for line in open(path, encoding="utf-8"):
        parts = line.split()
        if not parts:
            continue
        w = parts[0].lower().replace("’", "'")
        c = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
        if w not in counts:
            counts[w] = c
    total = sum(counts.values())
    words = list(counts)[:n]
    return words, {w: c / total for w, c in counts.items()}


def load_vectors(path, wanted=None):
    """Unit-normalised vectors for `wanted` words, or every word if None."""
    vecs = {}
    with open(path, encoding="utf-8", errors="ignore") as f:
        next(f)  # header: "<count> <dim>"
        for line in f:
            w, rest = line.split(" ", 1)
            if (wanted is None or w in wanted) and w not in vecs:
                v = np.array(rest.split(), dtype=np.float32)
                vecs[w] = v / (np.linalg.norm(v) + 1e-9)
    return vecs


def tokenize(text):
    """Lowercase, split elisions (c'est -> c' est), keep sentence-final mark."""
    toks = TOKEN_RE.findall(text.lower().replace("’", "'"))
    end = "</.>"
    while toks and toks[-1][0] in ".!?…":
        mark = toks.pop()
        end = "</?>" if "?" in mark else "</!>" if "!" in mark else end
    return [PAUSE if not t[0].isalpha() else t for t in toks], end


# ------------------------------------------------------- language model ---

class KneserNeyTrigram:
    """Interpolated Kneser-Ney trigram LM over a closed vocabulary.

    Also keeps 4-gram counts and sentence endings (last four words + end
    mark), used only as hard attestation filters.
    """

    def __init__(self, sentences, d=0.75):
        self.d = d
        self.tri = Counter()
        self.quad = Counter()
        self.tail = Counter(tuple(([BOS] * 4 + toks)[-5:]) for toks in sentences)
        for toks in sentences:
            seq = [BOS, BOS, BOS] + toks
            for i in range(3, len(seq)):
                self.tri[seq[i - 2], seq[i - 1], seq[i]] += 1
                self.quad[seq[i - 3], seq[i - 2], seq[i - 1], seq[i]] += 1
        self.bi = Counter()                 # raw bigram counts (for filtering)
        self.ctx2 = Counter()               # c(u, v, .)
        self.types2 = Counter()             # N1+(u, v, .)
        self.cont2 = Counter()              # N1+(., v, w)
        for (u, v, w), c in self.tri.items():
            self.bi[v, w] += c
            self.ctx2[u, v] += c
            self.types2[u, v] += 1
            self.cont2[v, w] += 1
        self.ctx1 = Counter()               # N1+(., v, .)
        self.types1 = Counter()             # N1+(v, .) over continuation counts
        self.cont1 = Counter()              # N1+(., w)
        for (v, w), c in self.cont2.items():
            self.ctx1[v] += c
            self.types1[v] += 1
            self.cont1[w] += 1
        self.cont1_total = sum(self.cont1.values())
        self.n_types = len(self.cont1) + 1

    def p_uni(self, w):
        return (self.cont1.get(w, 0) + 0.01) / (self.cont1_total + 0.01 * self.n_types)

    def p_bi(self, v, w):
        n = self.ctx1.get(v, 0)
        if not n:
            return self.p_uni(w)
        return (max(self.cont2.get((v, w), 0) - self.d, 0) / n
                + self.d * self.types1[v] / n * self.p_uni(w))

    def logp(self, u, v, w):
        n = self.ctx2.get((u, v), 0)
        if not n:
            return math.log(self.p_bi(v, w))
        p = (max(self.tri.get((u, v, w), 0) - self.d, 0) / n
             + self.d * self.types2[u, v] / n * self.p_bi(v, w))
        return math.log(p)


def ngram_hash(gram):
    return int.from_bytes(hashlib.blake2b(" ".join(gram).encode(), digest_size=8).digest(), "little", signed=True)


def build_lm(corpus_path, vocab, cache_dir):
    key = hashlib.sha1("\n".join(["v4", str(corpus_path), *vocab]).encode()).hexdigest()[:10]
    cache = cache_dir / f"lm_{key}.pkl"
    if cache.exists():
        with open(cache, "rb") as f:
            return pickle.load(f)
    vset = set(vocab)
    sents, closed = [], set()
    for line in open(corpus_path, encoding="utf-8"):
        text = line.rstrip("\n").split("\t")[-1]
        toks, end = tokenize(text)
        if not toks:
            continue
        mapped = [t if t in vset else (PAUSE if t == PAUSE else UNK) for t in toks]
        sents.append(mapped + [end])
        if UNK not in mapped and PAUSE not in mapped:
            closed.add(tuple(mapped + [end]))
    print(f"  trained LM on {len(sents):,} sentences "
          f"({len(closed):,} already fit the vocabulary)", file=sys.stderr)
    lm = KneserNeyTrigram(sents)
    lm.closed = closed
    # Hashes of every fully in-vocabulary 5-gram, to check finished sentences.
    five = set()
    for toks in sents:
        seq = [BOS] * 4 + toks
        for i in range(len(seq) - 4):
            gram = seq[i:i + 5]
            if UNK not in gram and PAUSE not in gram:
                five.add(ngram_hash(gram))
    lm.five = np.array(sorted(five), dtype=np.int64)
    # Sentence-level co-occurrence of content words, for PMI.
    lm.n_sents = len(sents)
    lm.df, lm.cooc = Counter(), Counter()
    for toks in sents:
        cw = sorted({t for t in toks if t in vset and t not in FUNCTION_WORDS})
        lm.df.update(cw)
        for i, a in enumerate(cw):
            for b in cw[i + 1:]:
                lm.cooc[a, b] += 1
    with open(cache, "wb") as f:
        pickle.dump(lm, f)
    return lm


# ------------------------------------------------------------ semantics ---

class Semantics:
    def __init__(self, vocab, vecs, prob, reference, theme_words, sif_a=1e-3):
        self.vocab = [w for w in vocab if w in vecs]
        self.vec = vecs
        self.dim = len(next(iter(vecs.values())))
        self.weight = {w: sif_a / (sif_a + prob.get(w, 1e-6)) for w in vecs}
        axis = np.mean([vecs[a] - vecs[b] for a, b in DRAMA_PAIRS if a in vecs and b in vecs], 0)
        axis /= np.linalg.norm(axis)
        ref = np.array([vecs[w] @ axis for w in reference if w in vecs])
        self.drama_z = {w: float((vecs[w] @ axis - ref.mean()) / ref.std()) for w in self.vocab}
        self.theme = None
        if theme_words:
            missing = [w for w in theme_words if w not in vecs]
            if missing:
                sys.exit(f"theme words without vectors: {missing} "
                         "(re-run fetch with a larger --vectors-top)")
            t = np.mean([vecs[w] for w in theme_words], 0)
            self.theme = t / np.linalg.norm(t)

    def sentence_vec(self, tokens):
        """SIF-weighted sum of word vectors (not normalised)."""
        v = np.zeros(self.dim, dtype=np.float32)
        for t in tokens:
            if t in self.vec:
                v += self.weight[t] * self.vec[t]
        return v

    def drama(self, tokens):
        """How far the most dramatic content word sits above ordinary words
        (0 for everyday sentences)."""
        zs = [self.drama_z[t] for t in tokens if t in self.drama_z and t not in FUNCTION_WORDS]
        return max(0.0, max(zs, default=0.0) - 1.0)

    def theme_score(self, tokens):
        if self.theme is None or not tokens:
            return 0.0
        v = self.sentence_vec(tokens)
        return float(v @ self.theme / (np.linalg.norm(v) + 1e-9))


class Situations:
    """Common everyday situations: spherical k-means over embeddings of a
    sample of corpus sentences. A situation's weight is its share of the
    sample, so frequent situations count for more."""

    def __init__(self, sem, corpus_path, k, sample, seed=0):
        rng = np.random.default_rng(seed)
        sents = []
        for line in open(corpus_path, encoding="utf-8"):
            toks, end = tokenize(line.rstrip("\n").split("\t")[-1])
            words = [t for t in toks if t != PAUSE]
            if 3 <= len(words) <= 12 and sum(t in sem.vec for t in words) >= 0.8 * len(words):
                sents.append((tuple(words), end))
        sents = [sents[i] for i in rng.choice(len(sents), min(sample, len(sents)), replace=False)]
        X = np.stack([sem.sentence_vec(w) for w, _ in sents])
        # SIF: remove the first principal component, the direction shared by
        # every sentence (mostly function words).
        self.pc = np.linalg.svd(X, full_matrices=False)[2][0]
        X = self._project(X)

        C = X[rng.choice(len(X), k, replace=False)].copy()
        for _ in range(25):
            assign = (X @ C.T).argmax(1)
            for j in range(k):
                total = X[assign == j].sum(0)
                if total.any():
                    C[j] = total / np.linalg.norm(total)
        self.centroids = C
        sizes = np.bincount(assign, minlength=k)
        self.weights = sizes / sizes.sum()

        # Label each situation with its most distinctive content words.
        df = Counter(t for w, _ in sents for t in set(w) if t not in FUNCTION_WORDS)
        sims = X @ C.T
        self.labels, self.examples = [], []
        for j in range(k):
            members = np.where(assign == j)[0]
            tf = Counter(t for i in members for t in set(sents[i][0]) if t not in FUNCTION_WORDS)
            keyness = {t: c * math.log(c * len(sents) / (len(members) * df[t]))
                       for t, c in tf.items() if c >= 3}
            self.labels.append(" / ".join(sorted(keyness, key=keyness.get, reverse=True)[:3]) or "-")
            self.examples.append(render(*sents[members[sims[members, j].argmax()]]) if len(members) else "")

    def _project(self, X):
        X = X - np.outer(X @ self.pc, self.pc)
        return X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)

    def embed(self, sem, token_lists):
        return self._project(np.stack([sem.sentence_vec(t) for t in token_lists]))

    def affinity(self, sem, token_lists, temperature):
        """Soft assignment of each sentence to situations (rows sum to 1).

        A generic sentence is about equally close to everything, so its
        membership is spread thin and it fully covers no situation; a
        specific sentence concentrates on the situation it serves."""
        logits = self.embed(sem, token_lists) @ self.centroids.T / temperature
        logits -= logits.max(1, keepdims=True)
        p = np.exp(logits)
        return p / p.sum(1, keepdims=True)


def build_situations(sem, corpus_path, vec_path, args):
    key = hashlib.sha1(f"s1|{corpus_path}|{vec_path}|{args.situations}|{args.sample}".encode()).hexdigest()[:10]
    cache = DATA / f"situations_{key}.pkl"
    if cache.exists():
        with open(cache, "rb") as f:
            return pickle.load(f)
    sit = Situations(sem, corpus_path, args.situations, args.sample)
    with open(cache, "wb") as f:
        pickle.dump(sit, f)
    return sit


# ------------------------------------------------------------ discourse ---

SPEAKER_DASH = re.compile(r"(?:^|\s)[-–—]\s*")


def speaker_turns(line):
    """A subtitle line can hold several speakers ("- Oui. - Non."): one list of
    sentences per speaker turn."""
    return [split_utterances(seg) for seg in SPEAKER_DASH.split(line) if seg.strip()]


def split_utterances(line):
    """Returns [(tokens, end)] for each sentence in the text, with internal
    pauses kept as ","."""
    out, cur = [], []
    for t in TOKEN_RE.findall(line.lower().replace("’", "'")):
        if t[0] in ".!?…":
            while cur and cur[-1] == ",":
                cur.pop()
            if cur:
                out.append((cur, "</?>" if "?" in t else "</!>" if "!" in t else "</.>"))
            cur = []
        elif t[0].isalpha():
            cur.append(t)
        elif t in ",;:" and cur and cur[-1] != ",":
            cur.append(",")
    while cur and cur[-1] == ",":
        cur.pop()
    if cur:
        out.append((cur, "</.>"))
    return out


def utterance_features(toks, end, vset):
    """Features a line passes to the next: its content words, first word,
    speech act and grammatical person."""
    feats = {"w:" + t for t in toks if t in vset and t not in FUNCTION_WORDS}
    if toks[0] in vset:
        feats.add("first:" + toks[0])
    feats.add("act:" + speech_act(toks, end))
    feats.add("p:" + (person(toks) or "-"))
    return feats


class Discourse:
    """Sentence-ordering model: PMI(feature of sentence i, feature of
    sentence i+1) over consecutive sentences of the same speaker turn, in the
    style of Lapata (2003). Also counts how often each in-vocabulary line is
    said."""

    def __init__(self, subs_path, vocab, min_count=5):
        vset = set(vocab)
        ids = {}
        self.freq = Counter()
        codes, chunks = [], []
        for line in open(subs_path, encoding="utf-8", errors="ignore"):
            for turn in speaker_turns(line):
                prev = None                     # pairs never cross a speaker change
                for toks, end in turn:
                    if all(t in vset or t == "," for t in toks):
                        self.freq[tuple(toks), end] += 1
                    cur = [ids.setdefault(f, len(ids)) for f in utterance_features(toks, end, vset)]
                    if prev:
                        codes.extend((a, b) for a in prev for b in cur)
                    prev = cur
            if len(codes) > 1_000_000:
                chunks.append(np.array(codes, dtype=np.int32))
                codes = []
        chunks.append(np.array(codes, dtype=np.int32).reshape(-1, 2))
        pairs = np.concatenate([c.reshape(-1, 2) for c in chunks])
        F = len(ids)
        counts = np.bincount(pairs[:, 0].astype(np.int64) * F + pairs[:, 1], minlength=F * F).reshape(F, F)
        n = counts.sum()
        prev_c, next_c = counts.sum(1, keepdims=True), counts.sum(0, keepdims=True)
        with np.errstate(divide="ignore", invalid="ignore"):
            pmi_ = np.log(counts * n / (prev_c * next_c))
        pmi_[counts < min_count] = 0.0           # unseen or rare: neutral
        self.pmi = np.clip(pmi_, -2, 4).astype(np.float32)
        self.ids = ids
        self.n_pairs = int(n)
        print(f"  discourse model: {self.n_pairs:,} feature pairs, {len(self.freq):,} "
              "distinct in-vocabulary lines", file=sys.stderr)

    def transitions(self, sentences, vset):
        """Matrix T[i, j]: how well sentence j follows sentence i (mean PMI)."""
        M = np.zeros((len(sentences), len(self.ids)), dtype=np.float32)
        for i, p in enumerate(sentences):
            fs = [self.ids[f] for f in utterance_features(list(p.toks), p.end, vset) if f in self.ids]
            if fs:
                M[i, fs] = 1.0 / len(fs)
        return M @ self.pmi @ M.T


def build_discourse(subs_path, vocab):
    key = hashlib.sha1("\n".join(["d2", str(subs_path), *vocab]).encode()).hexdigest()[:10]
    cache = DATA / f"discourse_{key}.pkl"
    if cache.exists():
        with open(cache, "rb") as f:
            return pickle.load(f)
    disc = Discourse(subs_path, vocab)
    with open(cache, "wb") as f:
        pickle.dump(disc, f)
    return disc


# --------------------------------------------------------------- search ---

def render(tokens, end):
    out = ""
    for t in tokens:
        out += ("" if not out or out.endswith("'") or t == "," else " ") + t
    return out[:1].upper() + out[1:] + ENDS[end]


def pmi(lm, a, b):
    """Pointwise mutual information of two words over corpus sentences."""
    c = lm.cooc.get((a, b) if a < b else (b, a), 0)
    return math.log(c * lm.n_sents / (lm.df[a] * lm.df[b])) if c else None


def zscore(xs):
    xs = np.array(xs, dtype=float)
    return (xs - xs.mean()) / (xs.std() + 1e-9)


@dataclass
class Sentence:
    toks: tuple
    end: str
    base: float             # generation score: fluency, coherence, theme, penalties
    fluency: float
    coherence: float
    theme: float
    seen: bool              # exact sentence already exists in the corpus
    leverage: float = 0.0   # weighted situation coverage
    situation: int = -1     # situation it serves best
    score: float = 0.0      # base + leverage, the final ranking score
    count: int = 0          # how often the line occurs in the subtitles

    @property
    def text(self):
        return render(self.toks, self.end)

    @property
    def negated(self):
        return is_negated(self.toks)

    @property
    def act(self):
        return speech_act(self.toks, self.end)


def beam_search(lm, sem, args):
    """Generate fluent sentences; returns Sentences sorted by generation score.

    At most --diversity beam entries may share their first two words (a simple
    diverse beam search), so the results are not one sentence with small
    variations.
    """
    words = sem.vocab
    ends = list(ENDS) if args.punct == "any" else [{".": "</.>", "!": "</!>", "?": "</?>"}[args.punct]]

    def coherence(toks):
        cw = [t for t in toks if t not in FUNCTION_WORDS]
        scores = [pmi(lm, a, b) for i, a in enumerate(cw) for b in cw[i + 1:]]
        return sum(scores) / len(scores) if scores else 0.0

    def coherent(toks, w):
        if w in FUNCTION_WORDS:
            return True
        for t in toks:
            if t in FUNCTION_WORDS:
                continue
            key = (t, w) if t < w else (w, t)
            if lm.cooc.get(key, 0) < args.min_cooc or pmi(lm, t, w) < args.min_pmi:
                return False
        return True

    def total(lm_sum, n, toks):
        fl, coh, res = lm_sum / n, coherence(toks), sem.theme_score(toks)
        penalty = (args.w_negation * is_negated(toks)
                   + args.w_anaphora * sum(t in ANAPHORA for t in toks)
                   + args.w_drama * sem.drama(toks))
        return (args.w_fluency * fl + args.w_coherence * coh + args.w_theme * res - penalty,
                fl, coh, res)

    def attested5(toks):
        seq = [BOS] * 4 + list(toks)
        hs = [ngram_hash(seq[i:i + 5]) for i in range(len(seq) - 4)]
        pos = np.searchsorted(lm.five, hs)
        return all(p < len(lm.five) and lm.five[p] == h for p, h in zip(pos, hs))

    def allowed(t, u, v, w):
        return (lm.bi.get((v, w), 0) >= args.min_bigram
                and lm.tri.get((u, v, w), 0) >= args.min_trigram
                and lm.quad.get((t, u, v, w), 0) >= args.min_fourgram)

    beam = [((), 0.0)]                     # (tokens, summed log-prob)
    finished = {}
    for step in range(args.max_len + 1):
        cands = []
        for toks, lp in beam:
            t, u, v = ((BOS, BOS, BOS) + toks)[-3:]
            if (len(toks) >= args.min_len and (not args.require_verb or VERBS & set(toks))
                    and not any(subj & set(toks) and tonic in toks for subj, tonic in SELF_CLASH)):
                question = toks[0] in QUESTION_OPENERS and (toks[0] != "qu'" or "est-ce" in toks)
                for e in (["</?>"] if question else ends):
                    if (allowed(t, u, v, e) and ((BOS,) * 4 + toks)[-4:] + (e,) in lm.tail
                            and (not args.strict5 or attested5(toks + (e,)))):
                        lp_e = lp + lm.logp(u, v, e)
                        s = total(lp_e, len(toks) + 1, list(toks))
                        if toks not in finished or s[0] > finished[toks][0][0]:
                            finished[toks] = (s, e)
            if len(toks) == args.max_len:
                continue
            for w in words:
                if w in toks or not allowed(t, u, v, w) or not coherent(toks, w):
                    continue
                nt = toks + (w,)
                nlp = lp + lm.logp(u, v, w)
                cands.append((total(nlp, len(nt), list(nt))[0], nt, nlp))
        if not cands:
            break
        cands.sort(key=lambda c: -c[0])
        beam, per_prefix = [], Counter()
        for _, nt, nlp in cands:
            if args.diversity:
                if per_prefix[nt[:2]] >= args.diversity:
                    continue
                per_prefix[nt[:2]] += 1
            beam.append((nt, nlp))
            if len(beam) == args.beam:
                break
    ranked = sorted(finished.items(), key=lambda kv: -kv[1][0][0])
    out = []
    for t, (sc, e) in ranked:
        seen = (*t, e) in lm.closed
        out.append(Sentence(t, e, sc[0] + args.w_attested * seen, *sc[1:], seen=seen))
    return out


def score_attested(lm, sem, args, toks, end):
    """Score a real sentence with the same terms as generated ones."""
    seq = (BOS, BOS) + tuple(PAUSE if t == "," else t for t in toks) + (end,)
    lp = sum(lm.logp(seq[i - 2], seq[i - 1], seq[i]) for i in range(2, len(seq)))
    fl = lp / (len(seq) - 2)
    cw = [t for t in toks if t not in FUNCTION_WORDS]
    pm = [pmi(lm, a, b) for i, a in enumerate(cw) for b in cw[i + 1:]]
    coh = sum(x for x in pm if x is not None) / len(pm) if pm else 0.0
    res = sem.theme_score(toks)
    base = (args.w_fluency * fl + args.w_coherence * coh + args.w_theme * res
            - args.w_negation * is_negated(toks)
            - args.w_anaphora * sum(t in ANAPHORA for t in toks)
            - args.w_drama * sem.drama(toks)
            + args.w_attested)
    return Sentence(tuple(toks), end, base, fl, coh, res, seen=True)


def attested_sentences(lm, sem, disc, args):
    """Real lines written entirely in the vocabulary: Tatoeba sentences and
    subtitle lines said at least twice. They are guaranteed natural."""
    out = []
    sources = [(sent[:-1], sent[-1]) for sent in lm.closed]
    sources += [(toks, end) for (toks, end), c in disc.freq.items() if c >= 2]
    for toks, end in sources:
        words = [t for t in toks if t != ","]
        if args.min_len <= len(words) <= args.max_len and len(set(words)) == len(words):
            out.append(score_attested(lm, sem, args, toks, end))
    return out


def candidates(lm, sem, sit, disc, args):
    """Generated plus attested sentences, deduplicated, with subtitle
    frequency added, ranked by leverage."""
    pool = {}
    for p in beam_search(lm, sem, args) + attested_sentences(lm, sem, disc, args):
        key = (p.toks, p.end)
        count = disc.freq.get(key, 0)
        # A line said several times in real dialogue is natural even when the
        # Tatoeba LM finds it unusual (e.g. lines opening with "Alors").
        if (p.fluency < args.min_fluency and count < args.trust_count) or RUDE & set(p.toks):
            continue
        if key not in pool or p.base > pool[key].base:
            pool[key] = p
    for p in pool.values():
        p.count = disc.freq.get((p.toks, p.end), 0)
        if p.count and not p.seen:
            p.seen, p.base = True, p.base + args.w_attested
        p.base += args.w_common * math.log1p(p.count)
    return rerank(list(pool.values()), sem, sit, args)


def rerank(pool, sem, sit, args):
    """Add leverage (weighted situation coverage) and sort by final score."""
    if not pool:
        return pool
    aff = sit.affinity(sem, [p.toks for p in pool], args.temperature)
    lev = aff @ sit.weights
    for p, l, lz, row in zip(pool, lev, zscore(lev), aff):
        p.leverage, p.situation = float(l), int(row.argmax())
        p.score = p.base + args.w_leverage * lz
    pool.sort(key=lambda p: -p.score)
    return pool


# ------------------------------------------------------------ monologue ---

# Discourse markers: fine inside a monologue, never as its first word.
CONNECTIVES = {"mais", "alors", "et", "donc", "parce", "ou", "puis", "enfin", "pourtant"}
# A line opening with a subordinator is a fragment unless a main clause
# follows the comma ("Si tu veux, je peux venir.").
SUBORDINATORS = {"si", "quand", "comme", "lorsqu'", "puisque", "puisqu'", "parce", "que", "qu'"}
# The word after one of these is almost always a finite verb ("je voyage").
SUBJECT_CLITICS = {"je", "j'", "tu", "il", "elle", "on", "nous", "vous", "ils", "elles",
                   "c'", "ne", "n'", "me", "m'", "te", "t'", "se", "s'", "y"}


def has_verb(toks):
    return any(t in VERBS for t in toks) or any(
        a in SUBJECT_CLITICS and b.isalpha() and b not in FUNCTION_WORDS for a, b in zip(toks, toks[1:]))


def stem(word):
    """Light stemming so travail / travailler / travaille count as one word."""
    return word[:5]

# Grammatical person of a sentence's subject, for speaker consistency.
PERSON = {"je": "1s", "j'": "1s", "tu": "2s", "nous": "1p", "vous": "2p", "on": "1p",
          "il": "3", "elle": "3", "ils": "3", "elles": "3"}
INFORMAL = {"tu", "te", "t'", "toi", "ton", "ta", "tes"}
FORMAL = {"vous", "votre", "vos"}


def person(toks):
    return next((PERSON[t] for t in toks if t in PERSON), None)


def plan_monologue(pool, sem, sit, disc, args):
    """Beam search over sentence sequences. Each line should be a likely
    continuation of the one before (learned from subtitles), stay on the
    monologue's topic, and be useful in itself. Returns [(score, [Sentence])]."""
    n = len(pool)
    vset = set(sem.vocab)
    flow = zscore(disc.transitions(pool, vset).ravel()).reshape(n, n)
    emb = sit.embed(sem, [p.toks for p in pool])
    aff = sit.affinity(sem, [p.toks for p in pool], args.temperature)
    w = sit.weights
    cov_scale = (aff @ w).std() + 1e-9

    quality = zscore([p.score for p in pool])
    topic = zscore([p.theme for p in pool]) if sem.theme is not None else np.zeros(n)
    persons = [person(p.toks) for p in pool]
    register = [("tu" if INFORMAL & set(p.toks) else "") + ("vous" if FORMAL & set(p.toks) else "")
                for p in pool]
    toks = [frozenset(p.toks) - {","} for p in pool]
    content = [frozenset(t for t in p.toks if t not in FUNCTION_WORDS) for p in pool]
    stems = [frozenset(stem(t) for t in c) for c in content]
    anaphors = [sum(t in ANAPHORA for t in p.toks) for p in pool]
    neg = [p.negated for p in pool]
    acts = [p.act for p in pool]

    # Main verb: first verb form in the line, for the contradiction check.
    verbs = [next((t for t in p.toks if t in VERBS), None) for p in pool]

    def redundant(i, j):
        overlap = len(toks[i] & toks[j]) / len(toks[i] | toks[j])
        a, b = pool[i].toks, pool[j].toks
        return overlap > args.max_overlap or a[:3] == b[:3] or a[-3:] == b[-3:]

    def contradicts(i, j):
        """Same subject and verb, opposite polarity: "Je ne peux pas faire ça."
        then "Je peux le faire." """
        return (verbs[i] and verbs[i] == verbs[j] and persons[i] == persons[j]
                and neg[i] != neg[j])

    # state: (ids, summed gain, tu/vous register, topic vector, best
    #         affinity per situation, speech acts used, content words said
    #         once, content words said twice or more)
    beam = [((), 0.0, "", np.zeros(emb.shape[1]), np.zeros(len(w)), frozenset(), frozenset(), frozenset())]
    finished = []
    for step in range(args.max_sentences):
        cands = []
        for idxs, acc, reg, centroid, best, used_acts, once, twice in beam:
            cov_gain = (np.maximum(aff, best) - best) @ w / cov_scale
            focus = emb @ (centroid / (np.linalg.norm(centroid) + 1e-9))
            n_neg = sum(neg[i] for i in idxs)
            prev = next((persons[i] for i in reversed(idxs) if persons[i]), None)
            for j in range(n):
                if j in idxs or (not idxs and pool[j].toks[0] in CONNECTIVES):
                    continue
                if register[j] == "tuvous" or (register[j] and reg and register[j] != reg):
                    continue                        # never mix tu and vous
                if neg[j] and (n_neg + 1 > max(1, (len(idxs) + 1) // 3) or (idxs and neg[idxs[-1]])):
                    continue                        # at most a third negated, never two in a row
                if acts[j] == "question" and idxs and acts[idxs[-1]] == "question":
                    continue                        # no two questions in a row
                if pool[j].toks[0] == "parce" and not (idxs and acts[idxs[-1]] == "question"):
                    continue                        # "parce que" answers a question
                if any(redundant(i, j) or contradicts(i, j) for i in idxs):
                    continue
                gain = (args.w_quality * quality[j] + args.w_topic * topic[j]
                        + args.w_coverage * cov_gain[j]
                        - args.w_overuse * len(stems[j] & twice))     # a third mention reads like a list
                if idxs:
                    gain += args.w_flow * flow[idxs[-1], j] + args.w_focus * focus[j]
                    gain += args.w_variety * (acts[j] not in used_acts)
                    if anaphors[j] and content[idxs[-1]]:
                        gain += args.w_anaphora * anaphors[j]   # il/elle now has an antecedent
                    if persons[j] and prev and persons[j] != prev:
                        gain -= args.w_person
                    if pool[idxs[-1]].toks[0] == pool[j].toks[0]:
                        gain -= args.w_monotony     # same first word as the previous line
                        if len(idxs) >= 2 and pool[idxs[-2]].toks[0] == pool[j].toks[0]:
                            gain -= 2 * args.w_monotony
                cands.append((idxs + (j,), acc + gain, reg or register[j], centroid + emb[j],
                              np.maximum(best, aff[j]), used_acts | {acts[j]},
                              once | stems[j], twice | (stems[j] & once)))
        if not cands:
            break
        cands.sort(key=lambda c: -c[1] / len(c[0]))
        beam = cands[:args.mono_beam]
        if step + 1 >= args.min_sentences:
            # Each sentence must earn its place, and attention wears thin: the
            # k-th line must add more than cost + fatigue * (k - 1).
            finished += [(acc - args.sentence_cost * len(idxs)
                          - args.fatigue * len(idxs) * (len(idxs) - 1) / 2, idxs)
                         for idxs, acc, *_ in beam]

    finished.sort(key=lambda f: -f[0])
    out, seen = [], set()
    for sc, idxs in finished:
        if frozenset(idxs) not in seen:
            seen.add(frozenset(idxs))
            out.append((sc, [pool[i] for i in idxs]))
    return out


# ---------------------------------------------------------------- setup ---

def load_models(args):
    freq = Path(args.freq) if args.freq else next(
        (p for p in [Path("fr_50.txt"), HERE / "fr_50.txt", DATA / "fr_50k.txt"] if p.exists()), None)
    vec_path = Path(args.vectors) if args.vectors else next(iter(sorted(DATA.glob("cc.fr.300.top*k.vec"))), None)
    corpus = Path(args.corpus) if args.corpus else DATA / "fra_sentences.tsv"
    subs = Path(args.subs) if args.subs else next(iter(sorted(DATA.glob("opensubtitles.fr.*.txt"))), None)
    for name, p in [("frequency list", freq), ("vectors", vec_path), ("corpus", corpus), ("subtitles", subs)]:
        if not p or not p.exists():
            sys.exit(f"missing {name}; run `python forge.py fetch` first")

    reference, prob = load_freq(freq, max(args.n, DRAMA_REFERENCE))
    vocab = reference[:args.n]
    theme = args.theme.lower().split() if args.theme else []
    sem = Semantics(vocab, load_vectors(vec_path), prob, reference, theme)
    if len(sem.vocab) < len(vocab):
        print(f"  no vectors for {len(vocab) - len(sem.vocab)} words", file=sys.stderr)
    lm = build_lm(corpus, sem.vocab, DATA)
    sit = build_situations(sem, corpus, vec_path, args)
    disc = build_discourse(subs, sem.vocab)
    print(f"\nvocabulary: top {len(sem.vocab)} words of {freq.name}"
          + (f" | theme: {' '.join(theme)}" if theme else ""))
    return sem, lm, sit, disc


def print_table(sentences, sit, numbered=False):
    print(("  # " if numbered else "")
          + f"{'score':>6} {'fluency':>7} {'lever':>6} {'said':>5}  {'act':<9} {'situation':<24} sentence")
    for k, p in enumerate(sentences, 1):
        print((f"{k:>3} " if numbered else "")
              + f"{p.score:6.2f} {p.fluency:7.2f} {p.leverage:6.3f} {p.count if p.seen else 'NEW':>5}  "
              f"{p.act:<9} {sit.labels[p.situation][:24]:<24} {p.text}")


def search(args):
    sem, lm, sit, disc = load_models(args)
    print_table(candidates(lm, sem, sit, disc, args)[:args.top], sit)


def situations(args):
    sem, lm, sit, disc = load_models(args)
    print(f"{len(sit.weights)} situations from {args.sample:,} corpus sentences\n")
    print(f"{'share':>6}  {'distinctive words':<34} example")
    for j in np.argsort(-sit.weights):
        print(f"{sit.weights[j]:6.1%}  {sit.labels[j][:34]:<34} {sit.examples[j]}")


def monologue(args):
    sem, lm, sit, disc = load_models(args)
    # The best few candidates from every situation, so the planner can reach
    # situations whose sentences are less fluent than the generic ones.
    # Lines opening with a connective (mais, alors...) are what make speech
    # flow, but rarely rank high on their own, so they get their own quota.
    per_sit, n_conn = Counter(), 0
    pool = []
    for p in candidates(lm, sem, sit, disc, args):
        opener = p.toks[1] if p.toks[0] in CONNECTIVES and len(p.toks) > 1 else p.toks[0]
        if opener in SUBORDINATORS and opener != "parce" and "," not in p.toks and p.end != "</?>":
            continue                            # "Si tu veux." / "Et si tu veux bien." are fragments
        if not has_verb(p.toks):
            continue                            # "Tout le monde." / "Et ta famille."
        if p.toks[0] in CONNECTIVES and n_conn < args.connective_lines:
            n_conn += 1
            pool.append(p)
        elif per_sit[p.situation] < args.per_situation:
            per_sit[p.situation] += 1
            pool.append(p)
    print(f"sentence pool: {len(pool)} candidates from {len(per_sit)} situations")
    results = plan_monologue(pool, sem, sit, disc, args)
    if not results:
        sys.exit("no monologue found; loosen --max-overlap or grow --pool")
    for rank, (sc, lines) in enumerate(results[:1 + args.alternatives]):
        label = "best monologue" if rank == 0 else f"alternative {rank}"
        print(f"\n=== {label}: {len(lines)} sentences, score {sc:.2f} ===\n")
        print(textwrap.fill(" ".join(p.text for p in lines), 78), "\n")
        if rank == 0 and len(lines) > 1:
            T = disc.transitions(lines, set(sem.vocab))
            print("flow between lines (PMI):", " ".join(f"{T[i, i + 1]:+.2f}" for i in range(len(lines) - 1)), "\n")
        if rank == 0:
            print_table(lines, sit, numbered=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="download frequency list, vectors and corpus")
    f.add_argument("--vectors-top", type=int, default=20000, help="how many fastText vectors to keep")
    f.add_argument("--subs-lines", type=int, default=3000000, help="subtitle lines to keep")
    f.set_defaults(func=fetch)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--freq", help="frequency list (default: fr_50.txt, else data/fr_50k.txt)")
    common.add_argument("--vectors", help="fastText .vec file (default: data/cc.fr.300.top*k.vec)")
    common.add_argument("--corpus", help="Tatoeba-style TSV, sentence in last column")
    common.add_argument("--subs", help="subtitle text, one line per row (default: data/opensubtitles.fr.*.txt)")
    common.add_argument("-n", type=int, default=100, help="vocabulary size (top-n words)")
    common.add_argument("--theme", help="space-separated words to steer meaning, e.g. 'voyage'")
    common.add_argument("--situations", type=int, default=60, help="number of situation clusters")
    common.add_argument("--sample", type=int, default=30000, help="corpus sentences to cluster")
    common.add_argument("--temperature", type=float, default=0.05,
                        help="softness of sentence-to-situation assignment")
    common.add_argument("--beam", type=int, default=300)
    common.add_argument("--diversity", type=int, default=3,
                        help="max beam entries sharing their first two words (0 = off)")
    common.add_argument("--min-len", type=int, default=2, help="min words per sentence")
    common.add_argument("--max-len", type=int, default=7, help="max words per sentence")
    common.add_argument("--min-bigram", type=int, default=2, help="bigram must occur this often in corpus")
    common.add_argument("--min-trigram", type=int, default=1, help="trigram must occur this often (0 = off)")
    common.add_argument("--min-fourgram", type=int, default=1, help="4-gram must occur this often (0 = off)")
    common.add_argument("--no-strict5", dest="strict5", action="store_false",
                        help="don't require every 5-gram of a finished sentence to be attested")
    common.add_argument("--min-cooc", type=int, default=3,
                        help="content-word pairs must share this many corpus sentences")
    common.add_argument("--min-pmi", type=float, default=1.0, help="minimum PMI between content words")
    common.add_argument("--no-verb", dest="require_verb", action="store_false", help="allow verbless sentences")
    common.add_argument("--punct", choices=["any", ".", "!", "?"], default="any")
    common.add_argument("--min-fluency", type=float, default=-2.6,
                        help="drop candidates whose mean log-prob per token is lower")
    common.add_argument("--trust-count", type=int, default=3,
                        help="subtitle lines said this often skip the fluency floor")
    common.add_argument("--w-fluency", type=float, default=3.0)
    common.add_argument("--w-coherence", type=float, default=0.3)
    common.add_argument("--w-theme", type=float, default=6.0)
    common.add_argument("--w-leverage", type=float, default=2.0, help="weight of situation coverage (z)")
    common.add_argument("--w-attested", type=float, default=1.0,
                        help="bonus for sentences that exist verbatim in the corpus")
    common.add_argument("--w-common", type=float, default=0.5,
                        help="weight of log subtitle frequency (how often the line is said)")
    common.add_argument("--w-negation", type=float, default=1.5, help="penalty for a negated sentence")
    common.add_argument("--w-drama", type=float, default=2.0,
                        help="penalty for dramatic words (violence, tragedy...)")
    common.add_argument("--w-anaphora", type=float, default=1.0, help="penalty per il/elle/lui...")

    s = sub.add_parser("search", parents=[common], help="find the highest-leverage sentence")
    s.add_argument("--top", type=int, default=15)
    s.set_defaults(func=search)

    c = sub.add_parser("situations", parents=[common], help="list the everyday situation clusters")
    c.set_defaults(func=situations)

    m = sub.add_parser("monologue", parents=[common], help="compose a variable-length monologue")
    m.add_argument("--per-situation", type=int, default=10, help="pool candidates kept per situation")
    m.add_argument("--min-sentences", type=int, default=3)
    m.add_argument("--max-sentences", type=int, default=16)
    m.add_argument("--mono-beam", type=int, default=100)
    m.add_argument("--max-overlap", type=float, default=0.4,
                   help="max word-set Jaccard overlap between any two sentences")
    m.add_argument("--min-quality", type=float, default=-0.5,
                   help="skip pool sentences whose score is this many std below the pool mean")
    m.add_argument("--w-quality", type=float, default=1.0, help="weight of each sentence's own score")
    m.add_argument("--w-flow", type=float, default=2.0, help="learned likelihood that a line follows the previous")
    m.add_argument("--w-focus", type=float, default=3.0, help="closeness to the monologue's running topic")
    m.add_argument("--w-coverage", type=float, default=0.3, help="new situations a sentence covers")
    m.add_argument("--w-variety", type=float, default=0.3, help="bonus for a new speech act")
    m.add_argument("--w-topic", type=float, default=2.0, help="per-sentence closeness to --theme")
    m.add_argument("--w-overuse", type=float, default=6.0,
                   help="penalty per content word mentioned for a third time")
    m.add_argument("--connective-lines", type=int, default=60,
                   help="pool slots reserved for lines opening with mais/alors/et...")
    m.add_argument("--w-monotony", type=float, default=2.0,
                   help="penalty for repeating the previous line's first word (x3 for a third time)")
    m.add_argument("--w-person", type=float, default=0.5, help="penalty when the subject's person changes")
    m.add_argument("--sentence-cost", type=float, default=6.0,
                   help="what each sentence must add to be included; lower = longer monologues")
    m.add_argument("--fatigue", type=float, default=0.6,
                   help="extra cost per line already said (diminishing returns)")
    m.add_argument("--alternatives", type=int, default=1)
    m.set_defaults(func=monologue)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
