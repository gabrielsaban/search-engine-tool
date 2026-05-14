"""Polite crawler for the quotes.toscrape.com coursework website."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from time import monotonic as default_monotonic
from time import sleep as default_sleep
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from requests import RequestException, Session

from indexer import Document

TARGET_URL = "https://quotes.toscrape.com/"
DEFAULT_POLITENESS_DELAY = 6.0
DEFAULT_TIMEOUT = 10.0


@dataclass(frozen=True)
class CrawlConfig:
    """Configuration for a polite crawl."""

    start_url: str = TARGET_URL
    politeness_delay: float = DEFAULT_POLITENESS_DELAY
    timeout: float = DEFAULT_TIMEOUT
    max_pages: int | None = None


@dataclass(frozen=True)
class CrawlError:
    """A recoverable error encountered while crawling one URL."""

    url: str
    message: str


@dataclass(frozen=True)
class CrawlResult:
    """Documents collected by a crawl, plus crawl diagnostics."""

    documents: list[Document] = field(default_factory=list)
    errors: list[CrawlError] = field(default_factory=list)
    visited_urls: tuple[str, ...] = ()


def crawl_site(
    config: CrawlConfig | None = None,
    *,
    session: Session | None = None,
    sleep: Callable[[float], None] = default_sleep,
    monotonic: Callable[[], float] = default_monotonic,
) -> CrawlResult:
    """Crawl quote pages by following pagination links."""
    crawl_config = config or CrawlConfig()
    http_session = session or Session()
    documents: list[Document] = []
    errors: list[CrawlError] = []
    visited: list[str] = []
    seen: set[str] = set()
    next_url: str | None = crawl_config.start_url
    last_request_at: float | None = None

    while next_url is not None and next_url not in seen:
        reached_page_limit = (
            crawl_config.max_pages is not None
            and len(visited) >= crawl_config.max_pages
        )
        if reached_page_limit:
            break

        _respect_politeness(
            last_request_at,
            crawl_config.politeness_delay,
            sleep=sleep,
            monotonic=monotonic,
        )
        current_url = next_url
        seen.add(current_url)
        visited.append(current_url)

        try:
            response = http_session.get(current_url, timeout=crawl_config.timeout)
            last_request_at = monotonic()
            response.raise_for_status()
        except RequestException as exc:
            errors.append(CrawlError(url=current_url, message=str(exc)))
            break

        documents.append(extract_document(current_url, response.text))
        next_url = extract_next_url(current_url, response.text)

        if next_url is not None and not _is_same_site(crawl_config.start_url, next_url):
            errors.append(
                CrawlError(
                    url=next_url,
                    message="Skipped pagination link outside the target site.",
                )
            )
            next_url = None

    return CrawlResult(
        documents=documents,
        errors=errors,
        visited_urls=tuple(visited),
    )


def extract_document(url: str, html: str) -> Document:
    """Extract indexable text from one quote page."""
    soup = BeautifulSoup(html, "html.parser")
    title = _normalise_text(soup.title.get_text(" ", strip=True) if soup.title else url)
    quote_texts = [
        _normalise_text(" ".join(_quote_parts(quote)))
        for quote in soup.select(".quote")
    ]
    text = " ".join(quote_texts).strip()

    if not text and soup.body is not None:
        text = _normalise_text(soup.body.get_text(" ", strip=True))

    return Document(url=url, title=title, text=text)


def extract_next_url(base_url: str, html: str) -> str | None:
    """Extract the absolute URL for the next page, if present."""
    soup = BeautifulSoup(html, "html.parser")
    next_link = soup.select_one("li.next a[href]")

    if next_link is None:
        return None

    href = next_link.get("href")
    if not href:
        return None

    return urljoin(base_url, href)


def _respect_politeness(
    last_request_at: float | None,
    politeness_delay: float,
    *,
    sleep: Callable[[float], None],
    monotonic: Callable[[], float],
) -> None:
    if last_request_at is None:
        return

    elapsed = monotonic() - last_request_at
    remaining_delay = politeness_delay - elapsed
    if remaining_delay > 0:
        sleep(remaining_delay)


def _quote_parts(quote) -> list[str]:
    parts = []

    if quote_text := quote.select_one(".text"):
        parts.append(quote_text.get_text(" ", strip=True))

    if author := quote.select_one(".author"):
        parts.append(author.get_text(" ", strip=True))

    parts.extend(tag.get_text(" ", strip=True) for tag in quote.select(".tag"))
    return parts


def _normalise_text(text: str) -> str:
    return " ".join(text.split())


def _is_same_site(start_url: str, next_url: str) -> bool:
    return urlparse(start_url).netloc == urlparse(next_url).netloc
