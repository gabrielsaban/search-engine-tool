# Search Engine Tool Roadmap

This roadmap is designed around the coursework marking criteria and the final 5-minute video demonstration. The goal is a small but professional Python search tool with clear evidence of crawling, indexing, searching, testing, version control, and critical GenAI reflection.

## Git Workflow

- `main`: stable branch; every merge should pass CI.
- `chore/project-foundation`: repository structure, dependencies, CI, README baseline, roadmap.
- `feat/indexer`: tokenisation and inverted index data model.
- `feat/search`: `print` and `find` query logic, including multi-word queries and ranking.
- `feat/crawler`: polite crawler for `https://quotes.toscrape.com/`, with error handling.
- `feat/cli`: interactive command-line shell with `build`, `load`, `print`, and `find`.
- `test/coverage-hardening`: edge cases, integration tests, coverage threshold, mocked network tests.
- `docs/submission-polish`: README, architecture notes, video script/checklist, GenAI reflection notes.

Use conventional commits throughout, for example:

- `chore: add ci workflow`
- `feat: build inverted index from crawled pages`
- `test: cover empty and unknown search queries`
- `docs: add command-line usage examples`

## Milestones

### 1. Project Foundation

- Create the required coursework structure: `src/`, `tests/`, `data/`.
- Add dependency files and Python tooling configuration.
- Add GitHub Actions CI for linting, formatting, tests, and coverage.
- Keep an initial green CI run so later regressions are visible.

### 2. Indexing Core

- Implement case-insensitive tokenisation.
- Store word frequency and positions per page.
- Save the inverted index in a simple file format suitable for inspection.
- Unit test punctuation, repeated words, mixed case, and empty content.

### 3. Search Core

- Implement `print <word>` to display a readable posting list.
- Implement `find <query terms>` for single and multi-word queries.
- Rank results using a justifiable scoring method, such as term frequency or TF-IDF.
- Handle empty queries and non-existent terms gracefully.

### 4. Crawler

- Crawl all reachable quote pages from the target site.
- Enforce a politeness window of at least 6 seconds between live requests.
- Parse quote page text using Beautiful Soup.
- Add retry/timeout/error handling.
- Test crawler behaviour with mocked HTTP responses so tests are fast.

### 5. CLI Integration

- Build an interactive shell around the four required commands.
- Implement `build`, `load`, `print`, and `find` end to end.
- Provide clear command feedback and error messages.
- Add integration tests for typical and edge-case CLI flows.

### 6. Quality Evidence

- Keep coverage above 85%.
- Run Ruff and pytest locally before each merge.
- Add complexity notes for the index and search operations.
- Keep commits small and meaningful.

### 7. Submission Package

- Finalise README with setup, usage, testing, design rationale, and dependencies.
- Generate the compiled index file in `data/`.
- Tag the final submission as `v1.0.0`.
- Prepare a 5-minute video script covering live demo, design, tests, Git workflow, and GenAI reflection.
