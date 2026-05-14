# Search Algorithm Research And Rationale

This document records the research decisions behind the coursework search engine.
It is written to support the implementation choices in `src/` and to make clear
which advanced ideas are implemented, adapted, or deliberately left out for this
small polite-crawled corpus.

## Implemented Retrieval Model

The project uses an inverted index: each normalised term points to a posting list
of pages where the term appears. Each posting stores:

- `frequency`: how often the term occurs in that page.
- `positions`: zero-based word positions for phrase matching.

This follows the standard information retrieval structure described by Manning,
Raghavan, and Schuetze: indexing first tokenises documents, normalises terms, and
creates a dictionary plus postings. The benefit is that search reads only the
posting lists for the query terms instead of scanning every crawled page.

For a normal multi-word query, the CLI uses Boolean AND semantics. For example:

```text
find good friends
```

returns pages that contain both `good` and `friends`. Internally this intersects
the posting lists for the query terms. For explicit alternatives, the parser
supports OR clauses:

```text
find indifference OR nonsense
```

Each OR clause is treated as its own AND query, and the final result set is the
union of the clause results.

## Ranking

Matched pages are ranked with a compact TF-IDF-style score:

```text
score(q, d) = sum(tf(t, d) * (ln((N + 1) / (df(t) + 1)) + 1))
```

Where:

- `tf(t, d)` is the frequency of term `t` in document `d`.
- `df(t)` is the number of documents containing term `t`.
- `N` is the number of indexed documents.

This mirrors the classical TF-IDF idea: repeated terms in a page strengthen that
page's score, while terms that occur in many pages are less discriminative.
Smoothing with `+ 1` keeps scores finite for the small corpus and avoids zeroing
out common but still useful terms. Final ties are sorted by URL so CLI output is
deterministic and testable.

## Phrase Queries

Quoted phrases use positional postings:

```text
find "good friends"
```

The search layer first finds pages containing all phrase terms, then checks
whether the second term appears at `first_position + 1`, the third at
`first_position + 2`, and so on. This matches the standard positional-index
approach to phrase queries and avoids false positives where all words appear on
the same page but not consecutively.

## Suggestions

If a query has no result, the CLI suggests close indexed terms using edit
distance over the indexed vocabulary. This is deliberately conservative:

- only unknown query terms are considered;
- candidate words must be within a small length gap;
- results are sorted by distance, then alphabetically.

This gives a useful "did you mean" behaviour without pretending to be semantic
search. It is appropriate for the small quote corpus and easy to test
deterministically.

## Considered Alternatives

BM25 was considered because it extends probabilistic retrieval with term
frequency and document-length normalisation. It is a stronger general-purpose
ranking baseline for larger collections, but the coursework corpus is only ten
short quote pages with similar structure. A transparent TF-IDF-style score is
easier to explain, avoids parameter tuning without relevance judgements, and is
sufficient for the current dataset. BM25 is a good candidate for the benchmarking
milestone because it can be compared against the current scorer.

PageRank and link analysis were considered but rejected for the current ranking
surface. PageRank estimates page importance from the web graph, but this site is
a small pagination chain where links mostly express navigation rather than
authority. Applying PageRank here would add complexity without meaningful ranking
signal.

Stemming and stopword removal were considered. Porter stemming can collapse
related variants such as plurals and suffixes, and stopword removal can shrink
the vocabulary. They are not enabled because this corpus contains short literary
quotes where exact wording matters, phrase search relies on preserved token
positions, and stopwords can be meaningful in quoted phrases. A later benchmark
could compare exact tokens against a stemmed index.

Skip pointers and compressed postings were considered. They improve traversal or
storage for large posting lists, but the current index is tiny and kept in memory.
The simpler dictionary-of-dictionaries representation is clearer for marking,
debugging, JSON persistence, and tests.

Concurrent crawling was considered but rejected for politeness. The target site
is small, and the coursework expects responsible crawling. A sequential crawler
with delay, timeout, same-site pagination, and deterministic tests gives stronger
evidence of engineering judgement than faster collection at unnecessary load.

Robots.txt handling is not implemented yet. RFC 9309 defines how crawlers should
interpret a site's `robots.txt`; for this coursework target, the crawler is
constrained to the specified site and uses a conservative delay. A production
extension should fetch and enforce `robots.txt` before crawling.

## Complexity Summary

Let:

- `T` be the total number of tokens across crawled pages.
- `V` be the number of unique indexed terms.
- `P(t)` be the posting list size for term `t`.
- `q` be the number of unique query terms in a clause.

Index construction is `O(T)` time because every token is processed once. The
in-memory index stores one dictionary entry per unique term and one posting per
term-page pair, plus positions for each token occurrence, so storage is
`O(V + T)`.

For an AND query, candidate discovery is proportional to the combined posting
lists for the queried terms rather than the full corpus. Phrase validation adds a
position check only for candidate pages. OR queries evaluate each clause and
merge results by URL.

Suggestion generation currently compares unknown terms with the indexed
vocabulary. If `V` is the vocabulary size and `m` and `n` are word lengths, the
worst case is `O(V * m * n)` per unknown term because edit distance uses dynamic
programming. This is acceptable for the current corpus and bounded in practice by
the length-gap filter.

## References

- Manning, Raghavan, and Schuetze, *Introduction to Information Retrieval*:
  inverted indexes, Boolean retrieval, positional indexes, TF-IDF, BM25, PageRank.
  https://nlp.stanford.edu/IR-book/
- Requests documentation: HTTP sessions, status handling, headers, and timeouts.
  https://requests.readthedocs.io/en/latest/
- Beautiful Soup documentation: HTML parsing and CSS selector support.
  https://www.crummy.com/software/BeautifulSoup/bs4/doc/
- RFC 9309, Robots Exclusion Protocol.
  https://www.ietf.org/rfc/rfc9309.html
- Porter stemming algorithm reference.
  https://snowballstem.org/algorithms/porter/stemmer.html
