# sentence-forge

Finds the highest-impact sentence, or composes a variable-length monologue,
from a strictly limited vocabulary (default: the top 100 French words).
It uses no LLM, only classical NLP.

V1 (single sentence only) is preserved on the `sentence-forge-v1` branch.

## Sentence generation

| Stage | Method |
|---|---|
| Vocabulary | top-N words of a frequency list (`word count` per line, e.g. `fr_50.txt`) |
| Fluency | interpolated Kneser-Ney trigram LM trained on Tatoeba French (~730k sentences) |
| Grammar filter | every bigram (≥2), trigram and 4-gram must be attested in the corpus; every 5-gram of a finished sentence too (hashed); the sentence may only end where its last four words have ended a real sentence; question openers force `?`; no "tu … toi" clashes |
| Coherence | every pair of content words must share ≥3 corpus sentences with PMI ≥ 1, which rejects long-range nonsense the n-grams can't see ("la route … mourir") |
| Meaning | fastText `cc.fr.300` vectors, SIF-weighted sentence vector |
| Impact | projection onto an intensity axis built from POS-matched seed pairs (`terrible − correct`, `toujours − parfois`, …), z-scored against the 5,000 most common words; plus optional cosine to a `--theme` |
| Search | beam search over the vocabulary; score = 3·fluency + 0.3·coherence + 0.5·intensity + 6·theme (weighted toward everyday French) |

## Monologue (V2)

1. **Pool:** a diverse beam search (at most 3 hypotheses per two-word prefix) collects up to 300 candidate sentences.
2. **Plan:** a second beam search over the pool builds sentence sequences. Each added sentence scores:

| Term | Meaning |
|---|---|
| quality | the sentence's own score (z-scored in the pool), ×2 |
| topic | closeness to `--theme` |
| cohesion | cosine between neighbouring sentence vectors (pool mean removed) |
| connective | small bonus for *mais / alors / et …* openers (never first) |
| person | penalty when the subject switches between je / tu / nous / il … |
| repeat | penalty per reused content word |

Hard rules: no near-duplicates (word Jaccard > 0.4, same first or last three
words), never mix *tu* and *vous*, no three questions in a row.

3. **Length:** each sentence costs `--sentence-cost` (default 2), so the
monologue grows only while the next line adds more than that. Length therefore
depends on how much good, compatible material the vocabulary and theme allow
(3 to 10 sentences by default). A small arc term rewards building toward a strong
last line.

## Run

```bash
pip install numpy
python forge.py fetch                    # ~90 MB: frequency list, Tatoeba, first 20k fastText vectors
python forge.py search                   # top-100 vocab, default scoring
python forge.py search --theme amour     # steer meaning toward a concept
python forge.py search -n 1000 --theme "voyage partir route"   # topics need a bigger vocab
python forge.py monologue                                      # top-100 vocab monologue
python forge.py monologue -n 1000 --theme "voyage partir"      # themed monologue
python forge.py monologue --sentence-cost 1 --max-sentences 15 # longer
python forge.py search --freq fr_50.txt -n 100 --max-len 9 --w-intensity 3 --show-vocab
```

The first search builds the LM in about 10s and caches it in `data/`. The
`in-corpus` column shows whether the exact sentence already exists in Tatoeba
(`NEW` means the search composed it).

The vector download only streams the head of the 1.2 GB fastText file: `.vec`
files are sorted by frequency, so the first 20k rows cover a small vocabulary.
