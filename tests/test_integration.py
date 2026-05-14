from crawler import CrawlResult
from indexer import Document
from main import SearchShell


def test_shell_build_load_print_find_flow(tmp_path) -> None:
    index_path = tmp_path / "index.json"

    def fake_crawler() -> CrawlResult:
        return CrawlResult(
            documents=[
                Document(
                    url="https://quotes.toscrape.com/page/1/",
                    title="Quotes Page 1",
                    text="Good friends and good books.",
                ),
                Document(
                    url="https://quotes.toscrape.com/page/2/",
                    title="Quotes Page 2",
                    text="Indifference is not friendship.",
                ),
            ],
            errors=[],
            visited_urls=(
                "https://quotes.toscrape.com/page/1/",
                "https://quotes.toscrape.com/page/2/",
            ),
        )

    shell = SearchShell(index_path=index_path, crawler=fake_crawler)

    assert shell.execute("build") == [
        "Crawled 2 page(s).",
        f"Indexed 8 unique term(s) and saved to {index_path}.",
    ]

    shell.search_index = None
    assert shell.execute("load") == [
        f"Loaded index from {index_path}.",
        "Index contains 8 unique term(s) across 2 page(s).",
    ]
    assert shell.execute("print indifference") == [
        "indifference",
        "https://quotes.toscrape.com/page/2/ | frequency=1 | positions=[0]",
    ]
    assert shell.execute("find good friends") == [
        "1. Quotes Page 1 | score=4.2164 | terms=good:2, friends:1 "
        "| https://quotes.toscrape.com/page/1/"
    ]


def test_shell_reports_no_results_for_absent_word_after_build(tmp_path) -> None:
    def fake_crawler() -> CrawlResult:
        return CrawlResult(
            documents=[
                Document(
                    url="https://quotes.toscrape.com/page/1/",
                    title="Quotes Page 1",
                    text="Good friends and good books.",
                )
            ],
            errors=[],
            visited_urls=("https://quotes.toscrape.com/page/1/",),
        )

    shell = SearchShell(index_path=tmp_path / "index.json", crawler=fake_crawler)
    shell.execute("build")

    assert shell.execute("print missing") == ["No postings found for 'missing'."]
    assert shell.execute("find missing") == ["No matching pages found."]
