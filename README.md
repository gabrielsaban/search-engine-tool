# Search Engine Tool

Python command-line search engine for the COMP3011 Web Services and Web Data coursework. The tool crawls [quotes.toscrape.com](https://quotes.toscrape.com/), builds an inverted index, saves it to disk, reloads it, and supports word and multi-word search from an interactive shell.

## Coursework Requirements Covered

- Crawls the target website: `https://quotes.toscrape.com/`
- Observes a default 6-second politeness delay between live requests.
- Builds an inverted index with word frequency and word positions per page.
- Treats search as case-insensitive.
- Saves and loads the compiled index from the filesystem.
- Provides the required commands: `build`, `load`, `print`, and `find`.
- Includes unit, integration, crawler, CLI, and synthetic-corpus tests.
- Uses GitHub Actions CI for linting, formatting, tests, and coverage.

## Repository Structure

```text
src/
  crawler.py      Polite crawler and HTML extraction
  indexer.py      Tokenisation, inverted index, JSON persistence
  search.py       Posting lookup, multi-term search, TF-IDF-style ranking
  main.py         Interactive command-line shell
tests/
  test_crawler.py
  test_indexer.py
  test_search.py
  test_main.py
  test_integration.py
  test_performance.py
data/
  index.json      Compiled index generated from the live target website
docs/
  *.md            Design notes, quality checklist, and testing notes
requirements.txt
requirements-dev.txt
pyproject.toml
```

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install runtime and development dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
```

The project uses Python 3.12 in CI.

## Running The CLI

Start the interactive shell:

```bash
PYTHONPATH=src python src/main.py
```

You should see:

```text
Search Engine Tool
Type 'help' for commands.
>
```

The default index path is:

```text
data/index.json
```

## Required Commands

### `build`

Crawls the live website, builds the inverted index, and saves it to `data/index.json`.

```text
> build
Crawled 10 page(s).
Indexed 849 unique term(s) and saved to data/index.json.
```

The default build uses a 6-second politeness delay between requests after the first request. A full crawl therefore takes about one minute.

### `load`

Loads the saved index from disk.

```text
> load
Loaded index from data/index.json.
Index contains 849 unique term(s) across 10 page(s).
```

### `print <word>`

Prints the posting list for a word, including frequency and positions.

```text
> print nonsense
nonsense
https://quotes.toscrape.com/page/2/ | frequency=1 | positions=[398]
https://quotes.toscrape.com/page/7/ | frequency=1 | positions=[293]
```

### `find <query terms>`

Finds pages containing all query terms and ranks them with a TF-IDF-style score.

```text
> find indifference
1. Quotes to Scrape | score=13.5237 | terms=indifference:5 | https://quotes.toscrape.com/page/2/
```

```text
> find good friends
1. Quotes to Scrape | score=22.7502 | terms=good:3, friends:8 | https://quotes.toscrape.com/page/2/
2. Quotes to Scrape | score=6.0506 | terms=good:1, friends:2 | https://quotes.toscrape.com/page/6/
```

## Extra CLI Commands

The shell also supports:

```text
help
exit
quit
```

These are provided for usability; the coursework-required commands remain `build`, `load`, `print`, and `find`.

## Development Smoke Tests

For a quick live smoke test without waiting for a full crawl:

```bash
PYTHONPATH=src python src/main.py --index-path data/dev-smoke-index.json --max-pages 1 --politeness-delay 0
```

Then run:

```text
build
print good
find life
exit
```

The `--politeness-delay 0` option is intended for development only. The default remains compliant with the coursework requirement.

## Design Overview

### Crawler

The crawler uses `requests` and Beautiful Soup. It extracts quote text, author names, and tags from each quote card, then follows the site's pagination links. It records recoverable request errors instead of crashing. The default `CrawlConfig` enforces a 6-second politeness delay between live requests.

### Inverted Index

The index maps each token to each page where it appears:

```python
{
    "good": {
        "https://quotes.toscrape.com/": {
            "frequency": 1,
            "positions": [95],
        }
    }
}
```

Page-level statistics are stored separately:

```python
{
    "https://quotes.toscrape.com/": {
        "title": "Quotes to Scrape",
        "total_terms": 228,
        "unique_terms": 134,
    }
}
```

Building the index is `O(total_terms)` because each token is processed once.

### Search

Queries reuse the same tokenisation rules as indexing. Multi-word queries use AND semantics, so `find good friends` returns pages containing both `good` and `friends`.

Results are scored with:

```text
term_frequency * (ln((document_count + 1) / (document_frequency + 1)) + 1)
```

Scores for all query terms are added together. Ties are ordered by URL for deterministic output.

## Testing

Run the full quality gate:

```bash
ruff check .
ruff format --check .
pytest --cov=src --cov-report=term-missing --cov-fail-under=85
```

Current local result at the time of writing:

```text
44 passed
coverage: 98.78%
```

Test coverage includes:

- Tokenisation and punctuation handling.
- Inverted index frequencies and positions.
- JSON save/load round trips.
- Missing, corrupt, and invalid index files.
- Single-word and multi-word search.
- TF-IDF-style ranking.
- CLI command parsing and validation.
- End-to-end shell build/load/print/find flow with fake crawler data.
- Crawler pagination, politeness, timeouts, HTTP errors, and external links using mocked HTTP responses.
- Synthetic corpus indexing/searching.

## Continuous Integration

GitHub Actions runs on pushes to project branches and pull requests into `main`.

The CI workflow checks:

- Dependency installation.
- Ruff linting.
- Ruff formatting.
- Pytest with coverage threshold `85%`.

## Documentation

Additional design notes:

- [Crawler design](docs/crawler-design.md)
- [Indexing design](docs/indexing-design.md)
- [Search design](docs/search-design.md)
- [CLI design](docs/cli-design.md)
- [Quality checklist](docs/quality-checklist.md)

## GenAI Declaration

This project was developed with assistance from OpenAI Codex/ChatGPT. GenAI was used for interpreting the brief, planning the roadmap, suggesting implementation structure, generating and refining tests, debugging failures, and improving documentation.

All generated code and suggestions were reviewed, tested, and modified as needed. Specific examples for critical reflection include:

- The project roadmap was derived from the coursework mark scheme so development produced evidence for testing, CI, documentation, version control, and the final video.
- An early squash merge reduced commit visibility on `main`; this was identified and the workflow changed to normal merge commits for later PRs.
- AI-assisted implementation was validated through unit tests, integration tests, mocked crawler tests, live smoke tests, and GitHub Actions.
- Mocked tests made crawler behaviour fast and deterministic, but live smoke tests were still needed to check the real target website.

The final video demonstration should include a critical evaluation of how GenAI helped and where its suggestions required human checking.

## Known Limitations

- Automated tests do not depend on the live website, so live availability is verified separately with smoke tests.
- The CLI is intentionally text-based because the brief requires a command-line interface.
- Query processing uses AND semantics for multi-word queries.
- Ranking is TF-IDF-style but intentionally compact and explainable for coursework scope.

## Submission Notes

The compiled index file is included at:

```text
data/index.json
```

Before submitting, check:

- The final video link is accessible in an incognito/private browser.
- The GitHub repository is public or accessible to markers.
- `data/index.json` is included in the repository and/or attached via Minerva.
- The video is under 5 minutes and covers live demo, design, testing, Git workflow, and GenAI reflection.
