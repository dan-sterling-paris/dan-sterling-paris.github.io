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
| Penalties | negation (−1.5), each context-dependent pronoun *il/elle/lui…* (−1.0); bonus for sentences attested verbatim (+1.0) |

## Monologue

1. **Pool:** the 6 best candidates from each situation.
2. **Select:** a beam search over sentence sequences maximises facility-location coverage of
   the situations (each new line should serve situations not yet covered), plus each line's
   own score and a bonus for a new speech act (question / request / statement / negation).
   Hard rules: at most a third of lines negated and never two in a row; no near-duplicates;
   never mix *tu* and *vous*; no three questions in a row.
3. **Length:** each line costs `--sentence-cost` (default 1.5), so the monologue grows only
   while the next line adds more than that.
4. **Order:** the chosen lines are re-ordered by greedy chaining, so neighbours
   share topic and speaker.

## Run

```bash
pip install numpy
python forge.py fetch                                # ~90 MB: frequency list, Tatoeba, first 20k fastText vectors
python forge.py situations                           # inspect the situation clusters
python forge.py search                               # best single sentences, top-100 vocab
python forge.py monologue -n 1000                    # monologue, top-1000 vocab
python forge.py monologue -n 1000 --theme voyage     # steer toward a topic
python forge.py monologue --sentence-cost 1 --max-sentences 15   # longer
```

The first run builds the LM and the situation clusters (about 15 s) and caches
them in `data/`.

The vector download only streams the head of the 1.2 GB fastText file: `.vec`
files are sorted by frequency, so the first 20k rows cover a small vocabulary.
