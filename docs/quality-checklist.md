# Quality Checklist

## Automated Checks

The project currently uses GitHub Actions and local commands to run:

- Ruff linting.
- Ruff formatting checks.
- Pytest.
- Coverage with an 85% minimum threshold.

Recommended local command before opening a pull request:

```bash
ruff check .
ruff format --check .
pytest --cov=src --cov-report=term-missing --cov-fail-under=85
```

## Test Coverage Areas

Current tests cover:

- Tokenisation rules and edge cases.
- Inverted index frequencies and word positions.
- Deterministic JSON save/load behaviour.
- Corrupt and structurally invalid saved index files.
- Single-term and multi-term search.
- TF-IDF-style ranking and deterministic tie-breaking.
- CLI command parsing and command validation.
- End-to-end shell build/load/print/find flow using fake crawler data.
- Crawler extraction, pagination, politeness, timeouts, HTTP errors, and external links.
- A synthetic corpus indexing/searching scenario.

## Live Smoke Testing

Automated tests do not depend on the live website. This keeps CI fast and reliable.

Manual smoke tests are still useful before submission:

```bash
PYTHONPATH=src python src/main.py --index-path data/dev-smoke-index.json --max-pages 1 --politeness-delay 0
```

Inside the shell:

```text
build
print good
find life
exit
```

For the final submission run, use the default politeness delay:

```bash
PYTHONPATH=src python src/main.py
```

Then run `build` and allow the crawler to wait at least 6 seconds between page requests.

Latest live smoke result:

- Ran the CLI against the live website with `--max-pages 2` and the default 6-second politeness delay.
- `build` crawled 2 pages and saved an index.
- `load` loaded the saved index successfully.
- `find indifference` returned a page 2 match.

## Known Limitations

- Automated crawler tests use mocked HTML and therefore do not prove the live site is available.
- The CLI is intentionally simple and text-based because the brief requires a command-line interface.
- Query processing uses AND semantics for multi-word queries. This is documented and matches the brief wording.
- Ranking uses a compact TF-IDF-style score rather than a full production search-engine ranking pipeline.
