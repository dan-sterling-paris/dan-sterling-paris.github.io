#!/usr/bin/env python3
"""sentence-forge: find the highest-impact sentence - or a whole monologue -
you can build from a strictly limited vocabulary, without an LLM.

Pipeline (all classical):
  1. Vocabulary  - the top-N words of a frequency list ("word count" per line).
  2. Fluency     - interpolated Kneser-Ney trigram LM trained on Tatoeba French,
                   plus hard filters: every bigram/trigram must be attested.
  3. Coherence   - every pair of content words must co-occur in corpus
                   sentences with positive PMI, so long-range combinations
                   the n-grams cannot see ("la route ... mourir") are rejected.
  4. Meaning     - fastText word vectors. Sentence vector = SIF-weighted mean.
                   Intensity = projection onto a semantic axis (strong - weak
                   seed words, SemAxis-style). Optional theme = cosine to a
                   theme centroid.
  5. Search      - beam search over the vocabulary, scoring every hypothesis
                   with fluency + coherence + intensity + theme.
  6. Monologue   - a diverse beam search fills a pool of sentences; a second
                   beam search over that pool orders them into a monologue of
                   variable length (cohesion between neighbours, no repetition,
                   an intensity arc that builds to the last line).

Usage:
  python forge.py fetch                         # download data into ./data
  python forge.py search                        # top-100 words, default scoring
  python forge.py search --theme amour --top 10
  python forge.py monologue -n 1000 --theme "voyage partir"
"""
import argparse
import bz2
import hashlib
import gzip
import math
import pickle
import re
import shutil
import sys
import urllib.request
import textwrap
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

FREQ_URL = "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/fr/fr_50k.txt"
VEC_URL = "https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.fr.300.vec.gz"
CORPUS_URL = "https://downloads.tatoeba.org/exports/per_language/fra/fra_sentences.tsv.bz2"

BOS, UNK, PAUSE = "<s>", "<unk>", "<p>"
ENDS = {"</.>": ".", "</!>": " !", "</?>": " ?"}

# Intensity axis (SemAxis-style): mean of (strong - weak) difference vectors.
# Each pair shares a part of speech so the axis measures force, not grammar.
# Pairs touching the search vocabulary are dropped at load time so the axis is
# not defined by the words it scores.
AXIS_PAIRS = [
    ("toujours", "parfois"), ("jamais", "rarement"), ("absolument", "plutôt"),
    ("totalement", "légèrement"), ("vraiment", "assez"), ("tout", "quelque"),
    ("terrible", "correct"), ("énorme", "moyen"), ("éternel", "temporaire"),
    ("extraordinaire", "ordinaire"), ("essentiel", "secondaire"),
    ("passion", "habitude"), ("vérité", "opinion"), ("guerre", "discussion"),
    ("terreur", "gêne"), ("mort", "fatigue"), ("adorer", "apprécier"),
    ("détruire", "modifier"),
]
AXIS_WORDS = {w for pair in AXIS_PAIRS for w in pair}
REFERENCE_SIZE = 5000   # intensity is z-scored against this many common words

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
peux peut veux veut sais sait""".split())

# A sentence opening with one of these (or containing est-ce) is a question.
QUESTION_OPENERS = {"pourquoi", "comment", "où", "quoi", "quand", "est-ce", "qu'"}

# A subject pronoun and its own stressed form in one generated sentence is
# almost always wrong ("Tu ne peux pas partir avec toi").
SELF_CLASH = [({"je", "j'"}, "moi"), ({"tu"}, "toi"), ({"il"}, "lui")]

LETTERS = "a-zàâäçéèêëîïôöùûüÿœæ"
TOKEN_RE = re.compile(rf"[{LETTERS}]+'|[{LETTERS}]+(?:-[{LETTERS}]+)*|[.!?]+|[,;:…«»()\"—–]")


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


def load_vectors(path, wanted):
    vecs = {}
    with open(path, encoding="utf-8", errors="ignore") as f:
        next(f)  # header: "<count> <dim>"
        for line in f:
            w, rest = line.split(" ", 1)
            if w in wanted and w not in vecs:
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
        self.weight = {w: sif_a / (sif_a + prob.get(w, 1e-6)) for w in self.vocab}
        vset = set(vocab)
        diffs = [vecs[a] - vecs[b] for a, b in AXIS_PAIRS
                 if a in vecs and b in vecs and a not in vset and b not in vset]
        axis = np.mean(diffs, 0)
        axis /= np.linalg.norm(axis)
        ref = np.array([float(vecs[w] @ axis) for w in reference if w in vecs])
        mu, sd = ref.mean(), ref.std()
        self.intensity = {w: (float(vecs[w] @ axis) - mu) / sd for w in self.vocab}
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
        return sum(self.weight[t] * self.vec[t] for t in tokens)

    def score(self, tokens):
        """Return (intensity, theme resonance) for a token list."""
        ws = [self.weight[t] for t in tokens]
        total = sum(ws) or 1.0
        inten = sum(w * self.intensity[t] for w, t in zip(ws, tokens)) / total
        res = 0.0
        if self.theme is not None:
            v = self.sentence_vec(tokens)
            res = float(v @ self.theme / (np.linalg.norm(v) + 1e-9))
        return inten, res


# --------------------------------------------------------------- search ---

def render(tokens, end):
    out = ""
    for t in tokens:
        out += ("" if not out or out.endswith("'") else " ") + t
    return out[:1].upper() + out[1:] + ENDS[end]


def pmi(lm, a, b):
    """Pointwise mutual information of two words over corpus sentences,
    or None if they co-occur fewer than --min-cooc times."""
    c = lm.cooc.get((a, b) if a < b else (b, a), 0)
    return math.log(c * lm.n_sents / (lm.df[a] * lm.df[b])) if c else None


@dataclass
class Sentence:
    toks: tuple
    end: str
    score: float
    fluency: float
    coherence: float
    intensity: float
    theme: float
    seen: bool          # exact sentence already exists in the corpus

    @property
    def text(self):
        return render(self.toks, self.end)


def beam_search(lm, sem, args, diversity=0):
    """Return finished Sentences, best first.

    With diversity > 0, at most that many beam entries may share their first
    two words (a simple diverse beam search), so the results are not one
    sentence with small variations.
    """
    words = sem.vocab
    ends = list(ENDS) if args.punct == "any" else [{"." : "</.>", "!": "</!>", "?": "</?>"}[args.punct]]

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
        inten, res = sem.score(toks) if toks else (0.0, 0.0)
        fl, coh = lm_sum / n, coherence(toks)
        return (args.w_fluency * fl + args.w_coherence * coh
                + args.w_intensity * inten + args.w_theme * res,
                fl, coh, inten, res)

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
            if diversity:
                if per_prefix[nt[:2]] >= diversity:
                    continue
                per_prefix[nt[:2]] += 1
            beam.append((nt, nlp))
            if len(beam) == args.beam:
                break
    ranked = sorted(finished.items(), key=lambda kv: -kv[1][0][0])
    return [Sentence(t, e, *sc, seen=(*t, e) in lm.closed) for t, (sc, e) in ranked]


# ------------------------------------------------------------ monologue ---

# Discourse markers: fine inside a monologue, never as its first word.
CONNECTIVES = {"mais", "alors", "et", "donc", "parce", "ou", "puis", "enfin",
               "pourtant", "si", "quand", "comme"}


# Grammatical person of a sentence's subject, for speaker consistency.
PERSON = {"je": "1s", "j'": "1s", "tu": "2s", "nous": "1p", "vous": "2p", "on": "1p",
          "il": "3", "elle": "3", "ils": "3", "elles": "3"}
INFORMAL = {"tu", "te", "t'", "toi", "ton", "ta", "tes"}
FORMAL = {"vous", "votre", "vos"}


def person(toks):
    return next((PERSON[t] for t in toks if t in PERSON), None)


def plan_monologue(pool, sem, args):
    """Beam search over sentence sequences; returns [(score, [Sentence])]."""
    n = len(pool)
    vecs = np.stack([sem.sentence_vec(p.toks) for p in pool])
    vecs -= vecs.mean(0)   # drop the component every everyday sentence shares
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9
    sim = vecs @ vecs.T

    def z(xs):
        xs = np.array(xs, dtype=float)
        return (xs - xs.mean()) / (xs.std() + 1e-9)

    quality = z([p.score for p in pool])
    topic = z([p.theme for p in pool]) if sem.theme is not None else np.zeros(n)
    persons = [person(p.toks) for p in pool]
    register = [("tu" if toks_ & INFORMAL else "") + ("vous" if toks_ & FORMAL else "")
                for toks_ in (set(p.toks) for p in pool)]
    inten = z([p.intensity for p in pool])
    toks = [frozenset(p.toks) for p in pool]
    content = [frozenset(t for t in p.toks if t not in FUNCTION_WORDS) for p in pool]

    def redundant(i, j):
        overlap = len(toks[i] & toks[j]) / len(toks[i] | toks[j])
        a, b = pool[i].toks, pool[j].toks
        return overlap > args.max_overlap or a[:3] == b[:3] or a[-3:] == b[-3:]

    def final(idxs, acc):
        k = len(idxs)
        arc = inten[idxs[-1]]                       # end on the strongest line
        if k > 1:
            arc += np.polyfit(range(k), inten[list(idxs)], 1)[0] * (k - 1)   # build up
        # Each sentence must earn its place: length is wherever the next
        # line would add less than --sentence-cost.
        return acc - args.sentence_cost * k + args.w_arc * arc

    # state: (sentence ids, summed gain, content words used, tu/vous register)
    beam = [((), 0.0, frozenset(), "")]
    finished = []
    for step in range(args.max_sentences):
        cands = []
        for idxs, acc, used, reg in beam:
            for j in range(n):
                if register[j] == "tuvous" or (register[j] and reg and register[j] != reg):
                    continue                        # never mix tu and vous
                if j in idxs or (not idxs and pool[j].toks[0] in CONNECTIVES):
                    continue
                if any(redundant(i, j) for i in idxs):
                    continue
                if pool[j].end == "</?>" and len(idxs) >= 2 and all(
                        pool[i].end == "</?>" for i in idxs[-2:]):
                    continue                        # no three questions in a row
                gain = (args.w_quality * quality[j] + args.w_topic * topic[j]
                        - args.w_repeat * len(content[j] & used))
                if idxs:
                    gain += args.w_cohesion * sim[idxs[-1], j]
                    prev = next((persons[i] for i in reversed(idxs) if persons[i]), None)
                    if persons[j] and prev and persons[j] != prev:
                        gain -= args.w_person
                    gain += args.w_connective * (pool[j].toks[0] in CONNECTIVES)
                cands.append((idxs + (j,), acc + gain, used | content[j], reg or register[j]))
        if not cands:
            break
        cands.sort(key=lambda c: -c[1] / len(c[0]))
        beam = cands[:args.mono_beam]
        if step + 1 >= args.min_sentences:
            finished += [(final(idxs, acc), idxs) for idxs, acc, _, _ in beam]

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
    for name, p in [("frequency list", freq), ("vectors", vec_path), ("corpus", corpus)]:
        if not p or not p.exists():
            sys.exit(f"missing {name}; run `python forge.py fetch` first")

    reference, prob = load_freq(freq, max(args.n, REFERENCE_SIZE))
    vocab = reference[:args.n]
    theme = args.theme.lower().split() if args.theme else []
    vecs = load_vectors(vec_path, set(reference) | AXIS_WORDS | set(theme))
    sem = Semantics(vocab, vecs, prob, reference, theme)
    if len(sem.vocab) < len(vocab):
        print(f"  no vectors for {len(vocab) - len(sem.vocab)} words", file=sys.stderr)
    lm = build_lm(corpus, sem.vocab, DATA)
    print(f"\nvocabulary: top {len(sem.vocab)} words of {freq.name}"
          + (f" | theme: {' '.join(theme)}" if theme else ""))
    return sem, lm


def print_table(sentences, numbered=False):
    print(f"{'#':>3} {'score':>6} {'fluency':>8} {'cohere':>7} {'intens':>7} {'theme':>6}  in-corpus  sentence"
          if numbered else
          f"{'score':>6} {'fluency':>8} {'cohere':>7} {'intens':>7} {'theme':>6}  in-corpus  sentence")
    for k, p in enumerate(sentences, 1):
        print((f"{k:>3} " if numbered else "")
              + f"{p.score:6.2f} {p.fluency:8.2f} {p.coherence:7.2f} {p.intensity:+7.2f} {p.theme:6.2f}"
              f"  {'yes' if p.seen else 'NEW':^9}  {p.text}")


def search(args):
    sem, lm = load_models(args)
    if args.show_vocab:
        ranked = sorted(sem.vocab, key=lambda w: -sem.intensity[w])
        print("intensity (z):", ", ".join(f"{w} {sem.intensity[w]:+.2f}" for w in ranked))
    print_table(beam_search(lm, sem, args)[:args.top])


def monologue(args):
    sem, lm = load_models(args)
    pool = beam_search(lm, sem, args, diversity=args.diversity)[:args.pool]
    print(f"sentence pool: {len(pool)} candidates")
    results = plan_monologue(pool, sem, args)
    if not results:
        sys.exit("no monologue found; loosen --max-overlap or grow --pool")
    for rank, (sc, lines) in enumerate(results[:1 + args.alternatives]):
        label = "best monologue" if rank == 0 else f"alternative {rank}"
        print(f"\n=== {label}: {len(lines)} sentences, score {sc:.2f} ===\n")
        print(textwrap.fill(" ".join(p.text for p in lines), 78), "\n")
        if rank == 0:
            print_table(lines, numbered=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="download frequency list, vectors and corpus")
    f.add_argument("--vectors-top", type=int, default=20000, help="how many fastText vectors to keep")
    f.set_defaults(func=fetch)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--freq", help="frequency list (default: fr_50.txt, else data/fr_50k.txt)")
    common.add_argument("--vectors", help="fastText .vec file (default: data/cc.fr.300.top*k.vec)")
    common.add_argument("--corpus", help="Tatoeba-style TSV, sentence in last column")
    common.add_argument("-n", type=int, default=100, help="vocabulary size (top-n words)")
    common.add_argument("--theme", help="space-separated words to steer meaning, e.g. 'amour'")
    common.add_argument("--beam", type=int, default=200)
    common.add_argument("--min-len", type=int, default=3, help="min words per sentence")
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
    common.add_argument("--w-fluency", type=float, default=3.0)
    common.add_argument("--w-coherence", type=float, default=0.3)
    common.add_argument("--w-intensity", type=float, default=0.5)
    common.add_argument("--w-theme", type=float, default=6.0)

    s = sub.add_parser("search", parents=[common], help="beam-search the highest-impact sentence")
    s.add_argument("--top", type=int, default=15)
    s.add_argument("--show-vocab", action="store_true", help="print per-word intensity scores")
    s.set_defaults(func=search)

    m = sub.add_parser("monologue", parents=[common], help="compose a variable-length monologue")
    m.add_argument("--pool", type=int, default=300, help="candidate sentences to plan with")
    m.add_argument("--diversity", type=int, default=3,
                   help="max pool beam entries sharing their first two words")
    m.add_argument("--min-sentences", type=int, default=3)
    m.add_argument("--max-sentences", type=int, default=10)
    m.add_argument("--mono-beam", type=int, default=100)
    m.add_argument("--max-overlap", type=float, default=0.4,
                   help="max word-set Jaccard overlap between any two sentences")
    m.add_argument("--w-quality", type=float, default=2.0, help="weight of each sentence's own score")
    m.add_argument("--w-cohesion", type=float, default=1.0, help="topical link between neighbours")
    m.add_argument("--w-topic", type=float, default=1.0, help="per-sentence closeness to --theme")
    m.add_argument("--w-person", type=float, default=1.5, help="penalty when the subject's person changes")
    m.add_argument("--w-connective", type=float, default=0.3, help="bonus for mais/alors/et... openers")
    m.add_argument("--w-repeat", type=float, default=0.3, help="penalty per reused content word")
    m.add_argument("--w-arc", type=float, default=0.3, help="reward for building to a strong last line")
    m.add_argument("--sentence-cost", type=float, default=2.0,
                   help="what each sentence must add to be included; lower = longer monologues")
    m.add_argument("--alternatives", type=int, default=2)
    m.set_defaults(func=monologue)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
