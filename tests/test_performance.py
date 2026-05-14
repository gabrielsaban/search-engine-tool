from indexer import Document, build_index
from search import find_pages


def test_index_and_search_synthetic_corpus() -> None:
    documents = [
        Document(
            url=f"https://quotes.toscrape.com/page/{page_number}/",
            title=f"Page {page_number}",
            text=(
                "wisdom courage curiosity "
                f"page{page_number} "
                f"{'rareterm ' if page_number == 17 else ''}"
            ),
        )
        for page_number in range(1, 101)
    ]

    search_index = build_index(documents)

    assert len(search_index.pages) == 100
    assert search_index.inverted_index["wisdom"][
        "https://quotes.toscrape.com/page/1/"
    ]["frequency"] == 1
    results = find_pages(search_index, "rareterm wisdom")

    assert len(results) == 1
    assert results[0].url == "https://quotes.toscrape.com/page/17/"
    assert results[0].term_frequencies == {"rareterm": 1, "wisdom": 1}
