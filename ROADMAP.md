# Search Engine Tool Roadmap

This roadmap is the working plan for the COMP3011 Web Services and Web Data coursework. It is intentionally structured around the marking criteria, because the target is not just a working command-line tool: the submission needs clear evidence of design understanding, testing, version-control discipline, and critical reflection on GenAI use.

## Target Outcome

Build a Python command-line search engine for `https://quotes.toscrape.com/` that can:

- Crawl every reachable quote page while respecting a politeness window of at least 6 seconds between live requests.
- Build an inverted index containing word statistics for each page.
- Save and load the compiled index from the filesystem.
- Support the required commands: `build`, `load`, `print <word>`, and `find <query terms>`.
- Handle edge cases gracefully and demonstrate them in the final video.
- Provide a comprehensive, fast test suite with coverage above 85%.
- Show incremental development through branches, conventional commits, pull requests, and CI.

## Marking Strategy

| Criterion | Weight | Evidence We Need |
| --- | ---: | --- |
| Crawling Implementation | 10% | Correct traversal of quote pages, 6-second politeness, timeout/error handling, crawler tests with mocked responses. |
| Indexing Implementation | 10% | Case-insensitive tokenisation, frequencies, positions, page-level statistics, clear data model. |
| Storage and Retrieval | 8% | Deterministic JSON index file, helpful errors for missing/corrupt files, `build` and `load` integration tests. |
| Search Functionality | 12% | `print` postings, single-word and multi-word `find`, ranking, empty/unknown query handling. |
| Testing and Coverage | 20% | Unit, integration, mocked network, edge-case, and selected performance tests; coverage above 85%. |
| Code Quality and Documentation | 10% | Modular `src/` structure, type hints, docstrings, README, complexity notes, restrained comments. |
| Version Control and Git Practices | 5% | Conventional commits, focused branches, CI, final tag, clean history visible in video. |
| Video Demonstration Quality | 10% | Prepared 5-minute script, reliable demo commands, readable terminal/code, clear narrative. |
| GenAI Critical Evaluation | 15% | Honest usage log, specific examples of help/hindrance, quality checks, learning reflection. |

## Git Workflow

`main` is the stable branch. Feature branches should be short lived and merged only after local checks pass. CI should run on pushes and pull requests.

Planned branches:

- `chore/project-foundation`: repository structure, dependencies, CI, roadmap, baseline tooling.
- `feat/indexer`: tokeniser, document model, inverted index builder, index serialisation shape.
- `feat/search`: query parser, `print`, `find`, multi-word matching, ranking.
- `feat/crawler`: requests/BeautifulSoup crawler, link discovery, politeness, error handling.
- `feat/cli`: interactive shell and command wiring.
- `test/coverage-hardening`: extra edge cases, integration tests, coverage and quality tightening.
- `docs/submission-polish`: README, architecture notes, GenAI reflection, video checklist.

Use conventional commits. Prefer several small commits over one large commit:

- `chore: add ci workflow`
- `test: cover tokenisation edge cases`
- `feat: record word positions in index`
- `feat: rank multi-term search results`
- `fix: handle missing index file gracefully`
- `docs: document command-line usage`

## Development Rules

- Keep `main` green.
- Run `ruff check .`, `ruff format --check .`, and `pytest --cov=src --cov-report=term-missing --cov-fail-under=85` before merging.
- Do not run live crawler tests in CI if they would wait for the 6-second politeness window. Use mocked HTTP responses for automated tests.
- Keep the generated index file under `data/` for submission evidence once the tool is complete.
- Record notable GenAI interactions as we go, especially when suggestions are changed, rejected, or verified by tests.

## Milestone 1: Project Foundation

Branch: `chore/project-foundation`

Goals:

- Create `src/`, `tests/`, `data/`, dependency files, and Python tooling config.
- Add GitHub Actions CI for linting, formatting, tests, and coverage.
- Add `.gitattributes` for consistent line endings.
- Add this roadmap as the shared planning document.

Acceptance criteria:

- Local lint and tests pass.
- CI workflow exists and is ready to run on GitHub.
- The branch has focused conventional commits.

Video evidence:

- Show the CI file and commit history briefly during the version-control section.

## Milestone 2: Indexing Core

Branch: `feat/indexer`

Implementation tasks:

- Define a small document representation, likely including `url`, `title`, `text`, and optional metadata.
- Implement case-insensitive tokenisation.
- Decide how to handle punctuation, apostrophes, hyphenated words, numbers, and repeated whitespace.
- Build the inverted index with this shape or similar:

```python
{
    "word": {
        "https://quotes.toscrape.com/page/1/": {
            "frequency": 3,
            "positions": [4, 18, 92],
        }
    }
}
```

- Store page statistics separately, such as total terms, unique terms, title, and crawl timestamp.
- Add deterministic JSON serialisation so saved files are inspectable.

Testing tasks:

- Tokenisation tests for case, punctuation, quotes, repeated spaces, and empty strings.
- Indexing tests for repeated words, positions, multiple pages, and no content.
- Serialisation tests for save/load round trips.

Acceptance criteria:

- Indexing is deterministic.
- Each indexed word stores per-page frequency and positions.
- Tests explain the intended behaviour through readable examples.

Full-marks stretch:

- Add type hints and docstrings to the public indexing functions.
- Add a short complexity note for indexing: roughly `O(total_terms)`.

## Milestone 3: Search Core

Branch: `feat/search`

Implementation tasks:

- Implement `print <word>` as a human-readable posting-list view.
- Implement `find <query terms>` for single and multi-word queries.
- Use case-insensitive query handling.
- Decide and document multi-word query semantics. The safest coursework interpretation is AND semantics: return pages containing all query terms.
- Rank results with a justifiable method:
  - Baseline: combined term frequency.
  - Stronger option: TF-IDF-style score using term frequency and inverse document frequency.
- Include snippets or matched-term summaries if they are easy to explain and do not clutter the CLI.

Testing tasks:

- Single-term query tests.
- Multi-term query tests.
- Ranking-order tests.
- Empty query tests.
- Unknown word tests.
- Mixed-case query tests.

Acceptance criteria:

- `print nonsense` works if the word exists and reports a clear message if it does not.
- `find indifference` returns matching pages.
- `find good friends` returns pages containing both terms, ordered by score.
- Empty input never crashes.

Full-marks stretch:

- Include a small ranking explanation in README.
- Keep ranking deterministic for ties, probably by URL.

## Milestone 4: Crawler

Branch: `feat/crawler`

Implementation tasks:

- Fetch pages with `requests`.
- Parse HTML using Beautiful Soup.
- Extract quote text, author names, tags, page title, and next-page links where useful.
- Follow internal pagination links until no new quote pages remain.
- Normalise URLs to avoid duplicate crawls.
- Enforce at least 6 seconds between successive live requests.
- Use timeouts and catch network exceptions.
- Return structured documents ready for indexing.

Testing tasks:

- Mock successful pages with `responses`.
- Mock pagination across multiple pages.
- Mock missing next link.
- Mock timeout or HTTP error behaviour.
- Test politeness without sleeping by injecting a fake clock/sleeper.

Acceptance criteria:

- Live `build` can crawl the target website politely.
- Tests are fast and do not depend on the live website.
- Error handling is visible and explainable.

Full-marks stretch:

- Add a `max_pages` or similar internal option for development/testing, while keeping default behaviour aligned with the brief.
- Log or print crawl progress in a concise way.

## Milestone 5: CLI Integration

Branch: `feat/cli`

Implementation tasks:

- Build an interactive shell around the required commands:
  - `build`
  - `load`
  - `print <word>`
  - `find <query terms>`
- Add `help` and `exit` for usability, while making clear that the four coursework commands are the required ones.
- Wire `build` to crawl, index, and save.
- Wire `load` to load from the default index path.
- Provide friendly errors for unknown commands, missing arguments, missing index file, and search before load/build.

Testing tasks:

- Test command parsing separately from command execution.
- Test build/load flows with fake crawler data.
- Test `print` and `find` output.
- Test unknown command and empty command handling.

Acceptance criteria:

- A marker can run the project from a fresh checkout using README instructions.
- The live demo commands are reliable and short enough for the 5-minute video.

Full-marks stretch:

- Add optional command-line flags such as `--index-path`, while keeping the interactive shell simple.

## Milestone 6: Quality Hardening

Branch: `test/coverage-hardening`

Implementation tasks:

- Review all edge cases against the marking bands.
- Add tests until coverage is comfortably above 85%.
- Add tests for corrupt index JSON and unavailable files.
- Add a small performance or benchmark-style test for indexing/searching synthetic documents.
- Run manual smoke tests on the live target website.

Acceptance criteria:

- CI passes consistently.
- Coverage remains above 85%.
- No live website dependency exists in automated CI tests.
- Known limitations are documented honestly.

Full-marks stretch:

- Add a small coverage badge or CI badge to README after GitHub Actions is active.
- Add a final quality checklist to the README or docs.

## Milestone 7: Documentation and Submission Polish

Branch: `docs/submission-polish`

README tasks:

- Project overview and coursework purpose.
- Installation and setup.
- All four command examples.
- Testing instructions.
- Dependency list.
- Architecture overview.
- Inverted index data structure explanation.
- Ranking explanation.
- Error-handling notes.
- GenAI declaration summary.

Submission tasks:

- Generate the compiled index file under `data/`.
- Confirm the index file is included or otherwise available for Minerva submission.
- Tag the final code as `v1.0.0`.
- Check repository visibility and sharing.
- Prepare the final Minerva text document containing the video link, GitHub repository URL, and index file details.

Video tasks:

- Prepare a timed script.
- Rehearse the live demo.
- Use a readable terminal font size.
- Check audio and screen resolution.
- Test the hosted video link in an incognito/private browser.

Acceptance criteria:

- The README is good enough for a marker to run the project without help.
- The video can be delivered under 5 minutes without rushing.
- GenAI use is declared honestly and critically.

## Five-Minute Video Plan

Target timings:

- `0:00-0:20`: state the project goal and target website.
- `0:20-2:20`: live demo of `build`, `load`, `print`, `find`, multi-word queries, and edge cases.
- `2:20-3:50`: code walkthrough covering crawler, indexer, search, and key design trade-offs.
- `3:50-4:20`: test suite and coverage run.
- `4:20-4:40`: Git workflow, branches, conventional commits, and CI.
- `4:40-5:00`: GenAI critical evaluation with one concrete benefit, one limitation, and one learning reflection.

Demo commands to prepare:

```text
build
load
print nonsense
find indifference
find good friends
find
find termthatdoesnotexist
```

## GenAI Reflection Log

Keep notes during development so the video reflection is specific rather than generic.

Suggested entries:

- Date.
- Tool used.
- What help was requested.
- What was useful.
- What was wrong, incomplete, or risky.
- How the final code was verified.
- What was learned by debugging or modifying the suggestion.

Likely reflection points:

- AI helped interpret the brief and convert the marking scheme into a roadmap.
- AI helped scaffold CI and testing strategy.
- Any AI-generated implementation must be validated with tests and manual explanation.
- If AI suggests over-engineering, simplify to match the coursework requirements.
- The student remains responsible for understanding every line submitted.

## Final Definition of Done

- All required commands work from a clean setup.
- Live build respects the 6-second politeness window.
- Index file is generated and available for submission.
- Tests pass locally and in GitHub Actions.
- Coverage is above 85%.
- README is complete and accurate.
- Git history shows regular, meaningful conventional commits.
- Final release tag exists.
- Video is under 5 minutes and covers all required sections.
- GenAI use is declared and critically evaluated.
