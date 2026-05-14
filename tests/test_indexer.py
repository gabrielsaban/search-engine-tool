import json

import pytest

from indexer import (
    Document,
    IndexLoadError,
    SearchIndex,
    build_index,
    load_index,
    save_index,
    tokenize,
)


def test_tokenize_normalises_case_and_punctuation() -> None:
    text = "Good friends, GOOD books -- that's a good life. Page 42!"

    assert tokenize(text) == [
        "good",
        "friends",
        "good",
        "books",
        "that's",
        "a",
        "good",
        "life",
        "page",
        "42",
    ]


def test_tokenize_returns_empty_list_for_blank_text() -> None:
    assert tokenize("  \n\t ") == []


def test_build_index_records_frequency_and_positions_per_page() -> None:
    documents = [
        Document(
            url="https://quotes.toscrape.com/page/1/",
            title="Quotes Page 1",
            text="Good friends and good books.",
        ),
        Document(
            url="https://quotes.toscrape.com/page/2/",
            title="Quotes Page 2",
            text="Friends are medicine.",
        ),
    ]

    search_index = build_index(documents)

    assert search_index.inverted_index["good"] == {
        "https://quotes.toscrape.com/page/1/": {
            "frequency": 2,
            "positions": [0, 3],
        }
    }
    assert search_index.inverted_index["friends"] == {
        "https://quotes.toscrape.com/page/1/": {
            "frequency": 1,
            "positions": [1],
        },
        "https://quotes.toscrape.com/page/2/": {
            "frequency": 1,
            "positions": [0],
        },
    }


def test_build_index_stores_page_statistics() -> None:
    document = Document(
        url="https://quotes.toscrape.com/page/1/",
        title="Quotes Page 1",
        text="Good friends and good books.",
    )

    search_index = build_index([document])

    assert search_index.pages["https://quotes.toscrape.com/page/1/"] == {
        "title": "Quotes Page 1",
        "total_terms": 5,
        "unique_terms": 4,
    }


def test_save_and_load_index_round_trip(tmp_path) -> None:
    search_index = SearchIndex(
        inverted_index={
            "good": {
                "https://quotes.toscrape.com/page/1/": {
                    "frequency": 2,
                    "positions": [0, 3],
                }
            }
        },
        pages={
            "https://quotes.toscrape.com/page/1/": {
                "title": "Quotes Page 1",
                "total_terms": 5,
                "unique_terms": 4,
            }
        },
    )
    index_path = tmp_path / "index.json"

    save_index(search_index, index_path)

    assert load_index(index_path) == search_index


def test_save_index_writes_deterministic_json(tmp_path) -> None:
    search_index = SearchIndex(
        inverted_index={
            "zebra": {
                "https://quotes.toscrape.com/page/2/": {
                    "frequency": 1,
                    "positions": [2],
                }
            },
            "apple": {
                "https://quotes.toscrape.com/page/1/": {
                    "frequency": 1,
                    "positions": [0],
                }
            },
        },
        pages={
            "https://quotes.toscrape.com/page/2/": {
                "title": "Quotes Page 2",
                "total_terms": 3,
                "unique_terms": 3,
            },
            "https://quotes.toscrape.com/page/1/": {
                "title": "Quotes Page 1",
                "total_terms": 4,
                "unique_terms": 4,
            },
        },
    )
    index_path = tmp_path / "index.json"

    save_index(search_index, index_path)

    saved_payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert list(saved_payload) == ["inverted_index", "pages"]
    assert list(saved_payload["inverted_index"]) == ["apple", "zebra"]


def test_load_index_rejects_non_object_json(tmp_path) -> None:
    index_path = tmp_path / "index.json"
    index_path.write_text("[]", encoding="utf-8")

    with pytest.raises(IndexLoadError, match="top-level JSON value"):
        load_index(index_path)
