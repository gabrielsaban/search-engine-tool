from indexer import Document, build_index, tokenize


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
