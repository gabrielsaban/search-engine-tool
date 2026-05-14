# Benchmarking Notes

The benchmark runner is designed to provide repeatable evidence for the
complexity claims in the README and final video. It avoids live crawling by using
either the committed index or a deterministic synthetic corpus.

## Commands

Saved index benchmark:

```bash
PYTHONPATH=src python3 benchmarks/search_benchmark.py --source saved
```

Synthetic benchmark:

```bash
PYTHONPATH=src python3 benchmarks/search_benchmark.py \
  --source synthetic \
  --documents 500 \
  --terms-per-document 120 \
  --vocabulary-size 1000
```

Custom query benchmark:

```bash
PYTHONPATH=src python3 benchmarks/search_benchmark.py \
  --source saved \
  --query "good friends" \
  --query '"good friends"'
```

## Example Local Output

Saved index on 2026-05-14:

```text
Search Engine Benchmark
Source: saved index: data/index.json

Index metrics:
  documents: 10
  unique_terms: 849
  postings: 1636
  positions: 2871
  index_json_bytes: 130999

Timings:
  index_or_load_seconds: 0.002879

Query timings:
  'good friends': 2 result(s), 0.096 ms
  '"good friends"': 1 result(s), 0.043 ms
  'indifference OR nonsense': 2 result(s), 0.028 ms
  'freinds': 0 result(s), 0.008 ms
```

Short synthetic smoke run on 2026-05-14:

```text
Search Engine Benchmark
Source: synthetic corpus: 50 documents, 40 terms/document, 100 vocabulary terms

Index metrics:
  documents: 50
  unique_terms: 164
  postings: 2000
  positions: 2000
  index_json_bytes: 142098

Timings:
  tokenisation_seconds: 0.000227
  index_or_load_seconds: 0.001907

Query timings:
  'shared topic7': 5 result(s), 0.104 ms
  '"alpha beta"': 10 result(s), 0.069 ms
  'rareterm17 shared': 2 result(s), 0.026 ms
  'missingterm': 0 result(s), 0.009 ms
```

Exact timings are machine-dependent, so the tests assert structure and result
counts rather than fixed latency numbers. The stable evidence is the shape of the
work: index construction scales with total token positions, saved index size
tracks stored postings and positions, and query timings are measured against the
posting lists touched by each query.

## Interpretation

- `documents` shows collection size.
- `unique_terms` shows dictionary size.
- `postings` counts term-page pairs.
- `positions` counts stored token positions and should track total indexed terms.
- `index_json_bytes` gives a deterministic persistence-size measure.
- `tokenisation_seconds` isolates token extraction for synthetic corpora.
- `index_or_load_seconds` measures either saved index loading or synthetic index
  construction.
- Query timings report result count and elapsed latency for representative AND,
  OR, phrase, rare-term, and missing-term searches.
