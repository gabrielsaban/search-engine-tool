from pytest import approx

from src.indexer import Document, build_index
from src.search import (
    SearchResult,
    TermContribution,
    explain_query,
    find_pages,
    format_postings,
    format_search_explanation,
    format_search_results,
    parse_query_terms,
    suggest_terms,
)


def sample_index():
    return build_index(
        [
            Document(
                url="https://quotes.toscrape.com/page/1/",
                title="Quotes Page 1",
                text="Good friends and good books make a good life.",
            ),
            Document(
                url="https://quotes.toscrape.com/page/2/",
                title="Quotes Page 2",
                text="Friends are the medicine of life.",
            ),
            Document(
                url="https://quotes.toscrape.com/page/3/",
                title="Quotes Page 3",
                text="Indifference is not friendship.",
            ),
        ]
    )


def test_parse_query_terms_reuses_index_tokenisation_rules() -> None:
    assert parse_query_terms("Good, FRIENDS -- that's all.") == [
        "good",
        "friends",
        "that's",
        "all",
    ]


def test_parse_query_terms_returns_empty_list_for_blank_query() -> None:
    assert parse_query_terms(" \n\t ") == []


def test_format_postings_for_existing_word() -> None:
    search_index = sample_index()

    assert format_postings(search_index, "GOOD") == [
        "good",
        "https://quotes.toscrape.com/page/1/ | frequency=3 | positions=[0, 3, 7]",
    ]


def test_format_postings_for_unknown_or_empty_word() -> None:
    search_index = sample_index()

    assert format_postings(search_index, "missing") == [
        "No postings found for 'missing'."
    ]
    assert format_postings(search_index, "") == ["No word provided."]


def test_find_pages_returns_empty_list_for_empty_or_unknown_query() -> None:
    search_index = sample_index()

    assert find_pages(search_index, "") == []
    assert find_pages(search_index, "missing") == []


def test_find_pages_finds_single_term_matches() -> None:
    search_index = sample_index()
    result = find_pages(search_index, "indifference")

    assert result == [
        SearchResult(
            url="https://quotes.toscrape.com/page/3/",
            title="Quotes Page 3",
            score=result[0].score,
            matched_terms=("indifference",),
            term_frequencies={"indifference": 1},
        )
    ]
    assert result[0].score == approx(1.6931, abs=0.0001)


def test_find_pages_uses_and_semantics_for_multi_word_queries() -> None:
    search_index = sample_index()
    result = find_pages(search_index, "good friends")

    assert result == [
        SearchResult(
            url="https://quotes.toscrape.com/page/1/",
            title="Quotes Page 1",
            score=result[0].score,
            matched_terms=("good", "friends"),
            term_frequencies={"good": 3, "friends": 1},
        )
    ]
    assert result[0].score == approx(6.3671, abs=0.0001)


def test_find_pages_matches_quoted_phrases_using_positions() -> None:
    search_index = sample_index()

    assert find_pages(search_index, '"good friends"') == [
        SearchResult(
            url="https://quotes.toscrape.com/page/1/",
            title="Quotes Page 1",
            score=6.3671,
            matched_terms=("good", "friends"),
            term_frequencies={"good": 3, "friends": 1},
        )
    ]


def test_find_pages_rejects_phrase_terms_that_are_not_adjacent() -> None:
    search_index = sample_index()

    assert find_pages(search_index, '"friends good"') == []


def test_find_pages_handles_phrase_case_and_punctuation() -> None:
    search_index = sample_index()

    assert find_pages(search_index, '"GOOD, friends!"')[0].url == (
        "https://quotes.toscrape.com/page/1/"
    )


def test_find_pages_supports_explicit_or_queries() -> None:
    search_index = sample_index()

    assert find_pages(search_index, "indifference OR friends") == [
        SearchResult(
            url="https://quotes.toscrape.com/page/3/",
            title="Quotes Page 3",
            score=1.6931,
            matched_terms=("indifference",),
            term_frequencies={"indifference": 1},
        ),
        SearchResult(
            url="https://quotes.toscrape.com/page/1/",
            title="Quotes Page 1",
            score=1.2877,
            matched_terms=("friends",),
            term_frequencies={"friends": 1},
        ),
        SearchResult(
            url="https://quotes.toscrape.com/page/2/",
            title="Quotes Page 2",
            score=1.2877,
            matched_terms=("friends",),
            term_frequencies={"friends": 1},
        ),
    ]


def test_find_pages_supports_or_with_phrases() -> None:
    search_index = sample_index()

    assert [
        result.url
        for result in find_pages(search_index, '"good friends" OR indifference')
    ] == [
        "https://quotes.toscrape.com/page/1/",
        "https://quotes.toscrape.com/page/3/",
    ]


def test_find_pages_orders_results_by_score_then_url() -> None:
    search_index = sample_index()

    assert find_pages(search_index, "friends") == [
        SearchResult(
            url="https://quotes.toscrape.com/page/1/",
            title="Quotes Page 1",
            score=1.2877,
            matched_terms=("friends",),
            term_frequencies={"friends": 1},
        ),
        SearchResult(
            url="https://quotes.toscrape.com/page/2/",
            title="Quotes Page 2",
            score=1.2877,
            matched_terms=("friends",),
            term_frequencies={"friends": 1},
        ),
    ]


def test_find_pages_deduplicates_repeated_query_terms() -> None:
    search_index = sample_index()
    result = find_pages(search_index, "good GOOD")

    assert result == [
        SearchResult(
            url="https://quotes.toscrape.com/page/1/",
            title="Quotes Page 1",
            score=result[0].score,
            matched_terms=("good",),
            term_frequencies={"good": 3},
        )
    ]
    assert result[0].score == approx(5.0794, abs=0.0001)


def test_format_search_results_for_matches() -> None:
    search_results = [
        SearchResult(
            url="https://quotes.toscrape.com/page/1/",
            title="Quotes Page 1",
            score=6.3671,
            matched_terms=("good", "friends"),
            term_frequencies={"good": 3, "friends": 1},
        )
    ]

    assert format_search_results(search_results) == [
        "1. Quotes Page 1 | score=6.3671 | "
        "terms=good:3, friends:1 | https://quotes.toscrape.com/page/1/"
    ]


def test_format_search_results_for_no_matches() -> None:
    assert format_search_results([]) == ["No matching pages found."]


def test_explain_query_returns_top_result_score_breakdown() -> None:
    search_index = sample_index()

    explanation = explain_query(search_index, "good friends")

    assert explanation is not None
    assert explanation.result.url == "https://quotes.toscrape.com/page/1/"
    assert explanation.term_contributions == (
        TermContribution(
            term="good",
            term_frequency=3,
            document_frequency=1,
            document_count=3,
            inverse_document_frequency=1.6931,
            contribution=5.0794,
        ),
        TermContribution(
            term="friends",
            term_frequency=1,
            document_frequency=2,
            document_count=3,
            inverse_document_frequency=1.2877,
            contribution=1.2877,
        ),
    )


def test_format_search_explanation_for_match() -> None:
    search_index = sample_index()
    explanation = explain_query(search_index, "good friends")

    assert format_search_explanation(explanation) == [
        "Top result: Quotes Page 1 | score=6.3671 | "
        "https://quotes.toscrape.com/page/1/",
        "Score breakdown:",
        "  good: tf=3, df=1/3, idf=1.6931, contribution=5.0794",
        "  friends: tf=1, df=2/3, idf=1.2877, contribution=1.2877",
        "Formula: score = sum(term_frequency * inverse_document_frequency)",
    ]


def test_format_search_explanation_for_no_match() -> None:
    assert format_search_explanation(None) == ["No matching pages found."]


def test_suggest_terms_finds_close_misspellings() -> None:
    search_index = sample_index()

    assert suggest_terms(search_index, "freinds") == ["friends"]


def test_suggest_terms_ignores_known_terms() -> None:
    search_index = sample_index()

    assert suggest_terms(search_index, "friends") == []
