"""Search helpers for querying an inverted index."""

from __future__ import annotations

from dataclasses import dataclass
from math import log
from re import finditer

from indexer import SearchIndex, tokenize


@dataclass(frozen=True)
class SearchResult:
    """A ranked page returned by a search query."""

    url: str
    title: str
    score: float
    matched_terms: tuple[str, ...]
    term_frequencies: dict[str, int]


@dataclass(frozen=True)
class QueryClause:
    """One AND-style query clause, optionally containing phrases."""

    terms: tuple[str, ...]
    phrases: tuple[tuple[str, ...], ...] = ()

    @property
    def all_terms(self) -> tuple[str, ...]:
        phrase_terms = [term for phrase in self.phrases for term in phrase]
        return tuple(_unique_terms([*self.terms, *phrase_terms]))


def parse_query_terms(query: str) -> list[str]:
    """Parse query text using the same tokenisation rules as the index."""
    return tokenize(query)


def parse_query_clause(query: str) -> QueryClause:
    """Parse one AND-style query clause with optional quoted phrases."""
    phrases = []
    query_without_phrases = query

    for match in finditer(r'"([^"]+)"', query):
        phrase_terms = tuple(tokenize(match.group(1)))
        if phrase_terms:
            phrases.append(phrase_terms)

    query_without_phrases = _remove_quoted_phrases(query_without_phrases)
    return QueryClause(
        terms=tuple(_unique_terms(tokenize(query_without_phrases))),
        phrases=tuple(phrases),
    )


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
    query_clauses = parse_query(query)
    results_by_url: dict[str, SearchResult] = {}

    for query_clause in query_clauses:
        terms = list(query_clause.all_terms)
        if not terms:
            continue

        candidate_urls = _candidate_urls(search_index, terms)
        phrase_matched_urls = {
            url
            for url in candidate_urls
            if _matches_all_phrases(search_index, url, query_clause.phrases)
        }

        for url in phrase_matched_urls:
            result = _build_search_result(search_index, url, terms)
            existing_result = results_by_url.get(url)
            if existing_result is None or result.score > existing_result.score:
                results_by_url[url] = result

    return sorted(
        results_by_url.values(), key=lambda result: (-result.score, result.url)
    )


def format_search_results(results: list[SearchResult]) -> list[str]:
    """Return readable lines for the find command."""
    if not results:
        return ["No matching pages found."]

    lines = []
    for position, result in enumerate(results, start=1):
        term_summary = ", ".join(
            f"{term}:{result.term_frequencies[term]}" for term in result.matched_terms
        )
        lines.append(
            f"{position}. {result.title} | score={result.score:.4f} "
            f"| terms={term_summary} | {result.url}"
        )

    return lines


def suggest_terms(
    search_index: SearchIndex,
    query: str,
    *,
    max_suggestions: int = 3,
) -> list[str]:
    """Suggest indexed terms for unknown query terms."""
    unknown_terms = [
        term
        for term in _unique_terms(parse_query_terms(query))
        if term not in search_index.inverted_index
    ]
    suggestions = []

    for unknown_term in unknown_terms:
        close_terms = sorted(
            (
                (term, _edit_distance(unknown_term, term))
                for term in search_index.inverted_index
                if _is_plausible_suggestion(unknown_term, term)
            ),
            key=lambda item: (item[1], item[0]),
        )
        suggestions.extend(term for term, _distance in close_terms[:max_suggestions])

    return _unique_terms(suggestions)[:max_suggestions]


def _unique_terms(terms: list[str]) -> list[str]:
    return list(dict.fromkeys(terms))


def parse_query(query: str) -> list[QueryClause]:
    """Parse a query into OR-separated clauses."""
    return [
        parse_query_clause(part) for part in _split_or_clauses(query) if part.strip()
    ]


def _split_or_clauses(query: str) -> list[str]:
    clauses = []
    current_clause = []
    current_word = []
    in_quote = False
    index = 0

    while index < len(query):
        character = query[index]
        if character == '"':
            in_quote = not in_quote
            current_word.append(character)
            index += 1
            continue

        if not in_quote and character.isspace():
            word = "".join(current_word)
            if word.lower() == "or":
                clauses.append("".join(current_clause).strip())
                current_clause = []
            else:
                current_clause.append(word)
                current_clause.append(character)
            current_word = []
            index += 1
            continue

        current_word.append(character)
        index += 1

    word = "".join(current_word)
    if word.lower() == "or":
        clauses.append("".join(current_clause).strip())
        current_clause = []
    else:
        current_clause.append(word)

    clauses.append("".join(current_clause).strip())
    return clauses


def _is_plausible_suggestion(unknown_term: str, indexed_term: str) -> bool:
    length_gap = abs(len(unknown_term) - len(indexed_term))
    if length_gap > 2:
        return False

    return _edit_distance(unknown_term, indexed_term) <= 2


def _edit_distance(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous_row = list(range(len(right) + 1))
    for left_index, left_character in enumerate(left, start=1):
        current_row = [left_index]
        for right_index, right_character in enumerate(right, start=1):
            insertion_cost = current_row[right_index - 1] + 1
            deletion_cost = previous_row[right_index] + 1
            substitution_cost = previous_row[right_index - 1] + (
                left_character != right_character
            )
            current_row.append(
                min(insertion_cost, deletion_cost, substitution_cost)
            )
        previous_row = current_row

    return previous_row[-1]


def _remove_quoted_phrases(query: str) -> str:
    return " ".join(part for part in query.split('"')[::2])


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
        term: search_index.inverted_index[term][url]["frequency"] for term in terms
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


def _matches_all_phrases(
    search_index: SearchIndex,
    url: str,
    phrases: tuple[tuple[str, ...], ...],
) -> bool:
    return all(_matches_phrase(search_index, url, phrase) for phrase in phrases)


def _matches_phrase(
    search_index: SearchIndex,
    url: str,
    phrase: tuple[str, ...],
) -> bool:
    if not phrase:
        return True

    first_term_positions = search_index.inverted_index[phrase[0]][url]["positions"]
    following_positions = [
        set(search_index.inverted_index[term][url]["positions"]) for term in phrase[1:]
    ]

    return any(
        all(
            start_position + offset in positions
            for offset, positions in enumerate(following_positions, start=1)
        )
        for start_position in first_term_positions
    )


def _score_result(
    search_index: SearchIndex,
    term_frequencies: dict[str, int],
) -> float:
    document_count = len(search_index.pages)
    score = 0.0

    for term, term_frequency in term_frequencies.items():
        document_frequency = len(search_index.inverted_index[term])
        inverse_document_frequency = (
            log((document_count + 1) / (document_frequency + 1)) + 1
        )
        score += term_frequency * inverse_document_frequency

    return round(score, 4)
