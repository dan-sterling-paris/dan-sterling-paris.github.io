# sentence-forge

Finds the highest-**leverage** sentence, or composes a variable-length
monologue, from a strictly limited vocabulary (default: the top 100 French
words). It uses no LLM, only classical NLP.

*Leverage* means usefulness in everyday life. Emotional force is not rewarded.
A sentence has leverage when it serves a common, real situation, stands on its
own without context, and is the kind of thing people actually say.

Earlier versions are kept on branches:
- `sentence-forge-v1`: a single sentence, scored on emotional intensity.
- `sentence-forge-v2`: adds monologues with a dramatic arc.
- `sentence-forge-v3`: everyday leverage; monologues chosen for breadth, so they read like phrase lists.

## Pipeline

| Stage | Method |
|---|---|
| Vocabulary | top-N words of a frequency list (`word count` per line, e.g. `fr_50.txt`) |
| Fluency | interpolated Kneser-Ney trigram LM trained on Tatoeba French (~730k sentences) |
| Grammar filter | attested 2/3/4-grams, hashed 5-grams and sentence endings; question openers force `?`; no "tu … toi" clashes |
| Coherence | content-word pairs must share ≥3 corpus sentences with PMI ≥ 1 |
| Candidates | real corpus sentences that already fit the vocabulary, plus new ones from a diverse beam search (≤3 per two-word prefix); mean log-prob ≥ −2.6 |
| Situations | 30k everyday corpus sentences, embedded as SIF-weighted fastText vectors with the first principal component removed, then clustered by spherical k-means into 60 situations weighted by frequency (`python forge.py situations`) |
| Leverage | soft assignment of the sentence to situations (softmax, T=0.05) weighted by situation frequency. Generic sentences spread thin and score low |
| Penalties | negation (−1.5), each context-dependent pronoun *il/elle/lui…* (−1.0), drama: projection on an intensity axis built from pairs like *guerre − discussion*, *mort − fatigue* (−2.0), rude words (removed) |
| Commonness | +0.5 · log(1 + times the line occurs in the subtitles); real lines (Tatoeba, or said ≥2× in subtitles) +1.0 |

## Monologue: making it flow

Choosing lines for breadth made V3 read like a phrase list. V4 learns how
people actually move from one sentence to the next.

1. **Discourse model:** about 3M lines of French film/TV subtitles (OpenSubtitles) are
   split into speaker turns. A dash marks a new speaker, so only consecutive sentences
   of the *same* speaker are paired. A sentence-ordering model in the style of
   Lapata (2003) learns PMI between features of one sentence and features of the
   next: content words, first word (*mais, alors, et…*), speech act and grammatical
   person.
2. **Pool:** the 10 best candidates per situation, plus 60 slots for lines opening
   with a connective. Fragments are dropped: subordinate openers (*si, quand, que…*)
   without a main clause, verbless lines, and *parce que* not answering a question.
3. **Plan:** a beam search adds one line at a time, scoring:

| Term | Meaning |
|---|---|
| flow (×2) | learned likelihood that the line follows the previous one |
| focus (×3) | closeness to the monologue's running topic |
| quality (×1) | the line's own score |
| topic (×2) | closeness to `--theme` |
| anaphora refund | *il/elle* is fine once the previous line gives it something to refer to |
| monotony (−2, −6) | same first word as the previous line (and the one before) |
| overuse (−6) | a word stem mentioned for the third time |
| person (−0.5) | the speaker's grammatical person changes |

   Hard rules: never mix *tu* and *vous*; at most a third negated, never two in a row;
   no two questions in a row; no near-duplicates; no contradictions (same subject and
   verb with opposite polarity).
4. **Length:** the k-th line must add more than `--sentence-cost` + `--fatigue` × (k − 1),
   so the monologue stops when the material runs thin (typically 5–10 lines).

## Run

```bash
pip install numpy
python forge.py fetch                                # ~200 MB: frequency list, Tatoeba, 20k fastText vectors, 3M subtitle lines
python forge.py situations                           # inspect the situation clusters
python forge.py search                               # best single sentences, top-100 vocab
python forge.py monologue -n 1000                    # monologue, top-1000 vocab
python forge.py monologue -n 1000 --theme voyage     # steer toward a topic
python forge.py monologue -n 1000 --sentence-cost 4  # longer
```

The first run builds the LM, the situation clusters and the discourse model
(about a minute per vocabulary size) and caches them in `data/`.

The vector download only streams the head of the 1.2 GB fastText file: `.vec`
files are sorted by frequency, so the first 20k rows cover a small vocabulary.
