# sentence-forge

Finds the highest-impact sentence that can be built from a strictly limited
vocabulary (default: the top 100 French words). It uses no LLM, only classical NLP:

| Stage | Method |
|---|---|
| Vocabulary | top-N words of a frequency list (`word count` per line, e.g. `fr_50.txt`) |
| Fluency | interpolated Kneser-Ney trigram LM trained on Tatoeba French (~730k sentences) |
| Grammar filter | every bigram (≥2), trigram and 4-gram in the output must be attested in the corpus |
| Meaning | fastText `cc.fr.300` vectors, SIF-weighted sentence vector |
| Impact | projection onto an intensity axis built from POS-matched seed pairs (`terrible − correct`, `toujours − parfois`, …), z-scored against the 5,000 most common words; plus optional cosine to a `--theme` |
| Search | beam search over the vocabulary; score = fluency + 1.5·intensity + 3·theme |

## Run

```bash
pip install numpy
python forge.py fetch                    # ~90 MB: frequency list, Tatoeba, first 20k fastText vectors
python forge.py search                   # top-100 vocab, default scoring
python forge.py search --theme amour     # steer meaning toward a concept
python forge.py search --freq fr_50.txt -n 100 --max-len 9 --w-intensity 3 --show-vocab
```

The first search builds the LM in about 10s and caches it in `data/`. The
`in-corpus` column shows whether the exact sentence already exists in Tatoeba
(`NEW` means the search composed it).

The vector download only streams the head of the 1.2 GB fastText file: `.vec`
files are sorted by frequency, so the first 20k rows cover a small vocabulary.
