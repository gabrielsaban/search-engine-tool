from pytest import approx

from indexer import Document, build_index
from search import (
    SearchResult,
    find_pages,
    format_postings,
    format_search_results,
    parse_query_terms,
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
