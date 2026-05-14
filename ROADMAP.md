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
- `feat/advanced-query-processing`: phrase search, OR queries, and term suggestions.
- `docs/search-research`: algorithm research notes and explicit design rationale.
- `feat/benchmarking`: reproducible performance evidence and complexity measurements.
- `chore/static-quality`: stricter code quality checks and publication polish.
- `release/v1.0.0`: release tag, release notes, and submission evidence.
- `docs/video-package`: final video script, demo checklist, and GenAI reflection notes.
- `feat/novel-search-insight`: a creative extension with tests and documentation.

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

## Outstanding-Band Implementation Plan

The following milestones are the remaining active development plan for targeting the excellent-to-outstanding grading band. They are intentionally scoped so each extension can be tested, documented, and explained, rather than added as superficial feature count.

## Milestone 8: Advanced Query Processing

Branch: `feat/advanced-query-processing`

Purpose:

Move the search behaviour from "very good" toward "excellent" by adding advanced query features that remain explainable in the video. This is an active implementation stage, not a wishlist.

Implementation tasks:

- Add quoted phrase search, for example `find "good friends"`.
- Use stored token positions to verify adjacent phrase matches.
- Add explicit OR query support with documented syntax.
- Add query suggestions for unknown terms using edit distance or close-prefix matches.
- Keep default multi-term behaviour as AND semantics unless explicitly changed by query syntax.
- Document query grammar and examples in README and search design notes.

Testing tasks:

- Phrase present on one page.
- Phrase terms present but not adjacent.
- Phrase with punctuation/case variation.
- Unknown term suggestions.
- Combined normal term and phrase query.
- Regression tests proving existing `find good friends` behaviour still works.

Acceptance criteria:

- Phrase search uses the existing positional index rather than ad hoc substring search.
- Query parsing is deterministic and documented.
- CLI output remains short and readable.
- Tests cover successful, unsuccessful, and edge-case queries.

Full-marks evidence:

- Demonstrates advanced query processing beyond the minimum brief.
- Shows direct use of stored word positions, strengthening the indexing design justification.

## Milestone 9: Search Algorithm Research And Rationale

Branch: `docs/search-research`

Purpose:

Provide explicit evidence of research into search-engine algorithms and modern practices.

Documentation tasks:

- Add `docs/SEARCH_RESEARCH.md`.
- Explain inverted indexes, posting lists, term frequency, document frequency, TF-IDF, Boolean retrieval, phrase queries, and optional stemming/stopword trade-offs.
- Compare implemented choices against alternatives such as PageRank, BM25, stemming, stopword removal, skip pointers, concurrent crawling, and compressed indexes.
- Explain why some advanced options are included and others are rejected for this small, polite-crawled corpus.
- Add references to module material, Requests, Beautiful Soup, Porter stemming, TF-IDF/BM25 background, and robots.txt/RFC material where relevant.

Acceptance criteria:

- Research notes are concise enough to read but technical enough to support an outstanding-band claim.
- Every advanced feature in the README is backed by implementation or explicitly described as a rejected alternative.
- The video can reference one or two research-informed trade-offs without getting lost.

Full-marks evidence:

- Clear design rationale rather than feature accumulation.
- Shows awareness of search-engine concepts beyond the required implementation.

## Milestone 10: Benchmarking And Complexity Evidence

Branch: `feat/benchmarking`

Purpose:

Turn the existing complexity notes into measured evidence.

Implementation tasks:

- Add a `benchmarks/` directory.
- Add a benchmark script that can:
  - Build or load an index.
  - Time tokenisation/indexing over synthetic corpora.
  - Time representative queries.
  - Report document count, unique terms, index size, and query latency.
- Ensure benchmark runs can skip live crawling by using the committed index or generated synthetic documents.
- Add benchmark instructions to README.

Testing tasks:

- Unit test benchmark helper functions without asserting machine-specific timings.
- Ensure benchmark script has `--help`.
- Keep benchmark out of normal CI timing assertions unless it is stable and quick.

Acceptance criteria:

- Benchmark output is reproducible enough to cite in docs/video.
- Complexity claims in README/docs are supported by examples.
- No benchmark requires violating politeness or live-site reliability.

Full-marks evidence:

- Supports the "highly optimised algorithms with complexity analysis and benchmarking" expectation.

## Milestone 11: Professional Static Quality

Branch: `chore/static-quality`

Purpose:

Raise the project from good Python coursework to a more professional open-source style.

Implementation tasks:

- Add `mypy` or `pyright` type checking if compatible with the current simple module layout.
- Add stricter Ruff rules where they improve clarity without causing churn.
- Consider a package layout only if it improves imports without conflicting with the brief's required `src/*.py` structure.
- Add docstrings where public functions/classes still need explanation.
- Review exception types and error messages for consistency.

Testing/CI tasks:

- Add static type checking to GitHub Actions.
- Keep local quality command documented.
- Ensure the CI runtime remains reasonable.

Acceptance criteria:

- Static analysis passes in CI.
- Type hints help explain the code rather than creating noisy ceremony.
- README quality commands match CI exactly.

Full-marks evidence:

- Supports "publication-quality code" and "professional-grade automated testing pipeline".

## Milestone 12: Release And Submission Evidence

Branch: `release/v1.0.0`

Purpose:

Create clear final-submission evidence without rushing the release before the video is ready.

Release tasks:

- Confirm final `data/index.json` was generated from a full polite crawl.
- Run a final live smoke test using the default 6-second delay.
- Run full local quality gate and confirm GitHub Actions is green.
- Create a Git tag such as `v1.0.0` only when the video/demo materials are ready.
- Draft GitHub release notes summarising features, tests, limitations, and submitted index details.
- Confirm repository visibility and README links.

Acceptance criteria:

- Final tag exists and points to the exact submitted code.
- Release notes are concise and accurate.
- The submitted index file matches the repository's `data/index.json`.

Full-marks evidence:

- Supports "professional Git workflow with semantic commits, tags/releases".

## Milestone 13: Outstanding Video And Reflection Package

Branch: `docs/video-package`

Purpose:

Turn the strong implementation into a strong 5-minute assessment performance.

Documentation tasks:

- Add `docs/video-script.md` with timestamped narration.
- Add `docs/demo-checklist.md` with exact commands and expected outputs.
- Add `docs/genai-reflection-notes.md` outside README so the reflection is present but not overloading the public project overview.
- Include specific GenAI examples:
  - Roadmap generated from the mark scheme.
  - Squash-merge issue corrected after review.
  - Tests used to validate and correct AI-assisted implementation.
  - Mocked crawler tests paired with live smoke testing.
- Add a final submission checklist for Minerva.

Acceptance criteria:

- Video script fits under 5 minutes.
- Demo commands are rehearsed and deterministic.
- GenAI evaluation is honest, specific, and critical.
- Reflection does not claim sole manual authorship where AI helped.

Full-marks evidence:

- Directly targets the 10% video and 15% GenAI criteria.
- Shows understanding, not just generated code.

## Milestone 14: Novel Contribution

Branch: `feat/novel-search-insight`

Purpose:

Add a creative feature that is genuinely useful and explainable, without destabilising the required commands.

Chosen direction:

- Query explanation mode showing why a page ranked first: term frequencies, IDF values, final score.
- Result snippets with matched terms.
- Query suggestions for misspelled words with "did you mean" output.

Selection criteria:

- Must build on the existing inverted index rather than bolting on unrelated code.
- Must be testable.
- Must be explainable in under 20 seconds in the video.
- Must not interfere with the four required commands.

Acceptance criteria:

- The novel search-insight feature is implemented, tested, and documented.
- README describes it briefly as an extension.
- The final video can mention it as evidence of creative extension after the required commands.

Full-marks evidence:

- Supports "novel contributions or particularly creative solutions" without risking the core coursework requirements.

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
