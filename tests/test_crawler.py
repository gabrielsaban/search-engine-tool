import responses
from requests import Session, Timeout

from src.crawler import CrawlConfig, crawl_site, extract_document, extract_next_url
from src.indexer import Document

PAGE_ONE = """
<html>
  <head><title>Quotes to Scrape</title></head>
  <body>
    <div class="quote">
      <span class="text">"The world as we have created it."</span>
      <small class="author">Albert Einstein</small>
      <div class="tags">
        <a class="tag">change</a>
        <a class="tag">world</a>
      </div>
    </div>
    <li class="next"><a href="/page/2/">Next</a></li>
  </body>
</html>
"""


PAGE_TWO = """
<html>
  <head><title>Quotes Page 2</title></head>
  <body>
    <div class="quote">
      <span class="text">"It is our choices."</span>
      <small class="author">J.K. Rowling</small>
      <div class="tags">
        <a class="tag">choices</a>
      </div>
    </div>
  </body>
</html>
"""


def test_extract_document_collects_quotes_authors_and_tags() -> None:
    document = extract_document("https://quotes.toscrape.com/", PAGE_ONE)

    assert document == Document(
        url="https://quotes.toscrape.com/",
        title="Quotes to Scrape",
        text=('"The world as we have created it." ' "Albert Einstein change world"),
    )


def test_extract_document_falls_back_to_body_text_without_quote_cards() -> None:
    html = """
    <html>
      <head><title>Plain Page</title></head>
      <body><main>Plain fallback content.</main></body>
    </html>
    """

    document = extract_document("https://quotes.toscrape.com/plain/", html)

    assert document == Document(
        url="https://quotes.toscrape.com/plain/",
        title="Plain Page",
        text="Plain fallback content.",
    )


def test_extract_next_url_resolves_relative_pagination_link() -> None:
    assert (
        extract_next_url("https://quotes.toscrape.com/", PAGE_ONE)
        == "https://quotes.toscrape.com/page/2/"
    )


def test_extract_next_url_returns_none_without_next_link() -> None:
    assert extract_next_url("https://quotes.toscrape.com/page/2/", PAGE_TWO) is None


def test_extract_next_url_returns_none_for_empty_href() -> None:
    html = '<html><body><li class="next"><a href="">Next</a></li></body></html>'

    assert extract_next_url("https://quotes.toscrape.com/", html) is None


@responses.activate
def test_crawl_site_follows_pagination_and_respects_politeness() -> None:
    responses.add(
        responses.GET,
        "https://quotes.toscrape.com/",
        body=PAGE_ONE,
        status=200,
    )
    responses.add(
        responses.GET,
        "https://quotes.toscrape.com/page/2/",
        body=PAGE_TWO,
        status=200,
    )
    sleep_calls: list[float] = []
    current_time = 0.0

    def fake_sleep(seconds: float) -> None:
        nonlocal current_time
        sleep_calls.append(seconds)
        current_time += seconds

    def fake_monotonic() -> float:
        return current_time

    result = crawl_site(
        CrawlConfig(start_url="https://quotes.toscrape.com/"),
        session=Session(),
        sleep=fake_sleep,
        monotonic=fake_monotonic,
    )

    assert [document.url for document in result.documents] == [
        "https://quotes.toscrape.com/",
        "https://quotes.toscrape.com/page/2/",
    ]
    assert result.errors == []
    assert sleep_calls == [6.0]
    assert responses.calls[0].request.headers["User-Agent"] == (
        "COMP3011-search-engine-tool/1.0"
    )


@responses.activate
def test_crawl_site_records_request_errors() -> None:
    responses.add(
        responses.GET,
        "https://quotes.toscrape.com/",
        body="Server error",
        status=500,
    )

    result = crawl_site(
        CrawlConfig(start_url="https://quotes.toscrape.com/"),
        session=Session(),
        sleep=lambda _seconds: None,
    )

    assert result.documents == []
    assert len(result.errors) == 1
    assert result.errors[0].url == "https://quotes.toscrape.com/"


@responses.activate
def test_crawl_site_can_limit_pages_for_development_runs() -> None:
    responses.add(
        responses.GET,
        "https://quotes.toscrape.com/",
        body=PAGE_ONE,
        status=200,
    )

    result = crawl_site(
        CrawlConfig(start_url="https://quotes.toscrape.com/", max_pages=1),
        session=Session(),
        sleep=lambda _seconds: None,
    )

    assert [document.url for document in result.documents] == [
        "https://quotes.toscrape.com/"
    ]
    assert result.visited_urls == ("https://quotes.toscrape.com/",)


@responses.activate
def test_crawl_site_skips_external_pagination_links() -> None:
    html = PAGE_ONE.replace("/page/2/", "https://example.com/page/2/")
    responses.add(
        responses.GET,
        "https://quotes.toscrape.com/",
        body=html,
        status=200,
    )

    result = crawl_site(
        CrawlConfig(start_url="https://quotes.toscrape.com/"),
        session=Session(),
        sleep=lambda _seconds: None,
    )

    assert len(result.documents) == 1
    assert len(result.errors) == 1
    assert result.errors[0].url == "https://example.com/page/2/"
    assert "outside the target site" in result.errors[0].message


@responses.activate
def test_crawl_site_records_timeout_errors() -> None:
    responses.add(
        responses.GET,
        "https://quotes.toscrape.com/",
        body=Timeout("request timed out"),
    )

    result = crawl_site(
        CrawlConfig(start_url="https://quotes.toscrape.com/"),
        session=Session(),
        sleep=lambda _seconds: None,
    )

    assert result.documents == []
    assert len(result.errors) == 1
    assert "request timed out" in result.errors[0].message
