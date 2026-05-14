# Release Notes: v1.0.0

Release date: 2026-05-14

## Summary

`v1.0.0` is the final coursework-ready release of the Search Engine Tool. It is a
Python command-line search engine for `https://quotes.toscrape.com/` with polite
crawling, positional indexing, persisted JSON storage, ranked search, advanced
query handling, benchmarking evidence, and CI-backed quality checks.

## Included Features

- Polite sequential crawler with a default 6-second delay between live requests.
- Beautiful Soup extraction for quote text, authors, tags, titles, and pagination.
- Positional inverted index storing term frequency and token positions.
- Deterministic JSON persistence in `data/index.json`.
- Required CLI commands: `build`, `load`, `print <word>`, and `find <query terms>`.
- Boolean AND search for multi-word queries.
- Quoted phrase search using stored token positions.
- Explicit `OR` queries.
- Close-term suggestions for misspelled searches.
- TF-IDF-style ranking with deterministic URL tie-breaking.
- Optional `explain <query>` command showing top-result score contributions.
- Reproducible benchmark runner for saved-index and synthetic-corpus evidence.

## Submitted Index

- Path: `data/index.json`
- Target: `https://quotes.toscrape.com/`
- Pages: 10
- Unique terms: 849
- Generated from a full polite crawl of the target site.

## Quality Evidence

Local and CI quality gates:

```bash
ruff check .
ruff format --check .
mypy
pytest --cov=src --cov-report=term-missing --cov-fail-under=85
```

Current local result:

```text
63 passed
coverage: 95.48%
```

## Known Limitations

- Automated tests use mocked HTTP rather than the live website.
- Phrase search is positional and does not include fuzzy phrase matching.
- `explain` describes the top-ranked result only, keeping CLI output concise.
- Ranking is intentionally compact and explainable rather than a production
  search-engine pipeline.
