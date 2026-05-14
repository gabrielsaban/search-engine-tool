"""Search helpers for querying an inverted index."""

from __future__ import annotations

from dataclasses import dataclass
from math import log

from indexer import SearchIndex, tokenize


@dataclass(frozen=True)
class SearchResult:
    """A ranked page returned by a search query."""

    url: str
    title: str
    score: float
    matched_terms: tuple[str, ...]
    term_frequencies: dict[str, int]


def parse_query_terms(query: str) -> list[str]:
    """Parse query text using the same tokenisation rules as the index."""
    return tokenize(query)


def format_postings(search_index: SearchIndex, word: str) -> list[str]:
    """Return a readable posting list for one word."""
    terms = parse_query_terms(word)
    if not terms:
        return ["No word provided."]

    term = terms[0]
    postings = search_index.inverted_index.get(term)
    if postings is None:
        return [f"No postings found for '{term}'."]

    lines = [term]
    for url in sorted(postings):
        posting = postings[url]
        lines.append(
            f"{url} | frequency={posting['frequency']} "
            f"| positions={posting['positions']}"
        )

    return lines


def find_pages(search_index: SearchIndex, query: str) -> list[SearchResult]:
    """Find pages containing all query terms."""
    terms = _unique_terms(parse_query_terms(query))
    if not terms:
        return []

    candidate_urls = _candidate_urls(search_index, terms)
    results = [
        _build_search_result(search_index, url, terms)
        for url in candidate_urls
    ]
    return sorted(results, key=lambda result: (-result.score, result.url))


def format_search_results(results: list[SearchResult]) -> list[str]:
    """Return readable lines for the find command."""
    if not results:
        return ["No matching pages found."]

    lines = []
    for position, result in enumerate(results, start=1):
        term_summary = ", ".join(
            f"{term}:{result.term_frequencies[term]}"
            for term in result.matched_terms
        )
        lines.append(
            f"{position}. {result.title} | score={result.score:.4f} "
            f"| terms={term_summary} | {result.url}"
        )

    return lines


def _unique_terms(terms: list[str]) -> list[str]:
    return list(dict.fromkeys(terms))


def _candidate_urls(search_index: SearchIndex, terms: list[str]) -> set[str]:
    matching_urls: set[str] | None = None

    for term in terms:
        term_urls = set(search_index.inverted_index.get(term, {}))
        if not term_urls:
            return set()

        if matching_urls is None:
            matching_urls = term_urls
        else:
            matching_urls &= term_urls

    return matching_urls or set()


def _build_search_result(
    search_index: SearchIndex,
    url: str,
    terms: list[str],
) -> SearchResult:
    term_frequencies = {
        term: search_index.inverted_index[term][url]["frequency"]
        for term in terms
    }
    score = _score_result(search_index, term_frequencies)
    page = search_index.pages[url]

    return SearchResult(
        url=url,
        title=page["title"],
        score=score,
        matched_terms=tuple(terms),
        term_frequencies=term_frequencies,
    )


def _score_result(
    search_index: SearchIndex,
    term_frequencies: dict[str, int],
) -> float:
    document_count = len(search_index.pages)
    score = 0.0

    for term, term_frequency in term_frequencies.items():
        document_frequency = len(search_index.inverted_index[term])
        inverse_document_frequency = log(
            (document_count + 1) / (document_frequency + 1)
        ) + 1
        score += term_frequency * inverse_document_frequency

    return round(score, 4)
