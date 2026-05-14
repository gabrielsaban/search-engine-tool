# Search Design Notes

## Query Parsing

Search queries reuse the indexer's tokenisation rules. This keeps indexing and searching consistent:

- Search is case-insensitive.
- Punctuation around words is ignored.
- Apostrophes inside words are preserved.
- Repeated query terms are deduplicated while preserving order.

## Multi-Word Queries

Multi-word queries use AND semantics. A query such as:

```text
find good friends
```

returns pages that contain both `good` and `friends`. This matches the coursework wording that the command should return pages containing the words in the query.

## Phrase And OR Queries

Quoted phrases use the word positions stored in the inverted index. A query such as:

```text
find "good friends"
```

returns pages where `good` is immediately followed by `friends`. Pages containing both terms in different positions are rejected for phrase queries.

Explicit `OR` splits the query into separate clauses:

```text
find indifference OR nonsense
```

returns pages matching either `indifference` or `nonsense`. Normal multi-word queries still use AND semantics unless `OR` is written explicitly.

When a query has no matches, the CLI suggests close indexed terms for misspellings, for example `freinds` -> `friends`.

## Ranking

Results are ranked with a small TF-IDF-style score:

```text
term_frequency * (ln((document_count + 1) / (document_frequency + 1)) + 1)
```

Scores for each query term are added together. This means:

- Words that appear more often on a page increase that page's score.
- Words that appear on fewer pages are treated as more distinctive.
- Ties are ordered by URL so output is deterministic.

The implementation rounds scores to four decimal places for stable command-line output and predictable tests.

## Score Explanation

The optional `explain <query>` command reuses the same search path as `find`, then expands the highest-ranked result into score components:

- term frequency on the page;
- document frequency across the index;
- inverse document frequency;
- per-term contribution to the final score.

This is a small search-insight extension. It makes the ranking transparent without changing the required `find` command or adding a separate scoring model.

## Complexity

For a query with `q` unique terms, candidate page discovery intersects posting lists for those terms. In the usual case, this is proportional to the combined size of the relevant posting lists rather than the number of all indexed words.
