"""Build and persist an inverted index for crawled web pages."""

from __future__ import annotations

import re
from dataclasses import dataclass
from json import JSONDecodeError, dump, load
from pathlib import Path
from typing import Any, TypedDict, cast

TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")


class Posting(TypedDict):
    """Statistics for one word on one page."""

    frequency: int
    positions: list[int]


class PageStats(TypedDict):
    """Summary statistics for one indexed page."""

    title: str
    total_terms: int
    unique_terms: int


InvertedIndex = dict[str, dict[str, Posting]]


class IndexLoadError(Exception):
    """Raised when a saved index cannot be loaded safely."""


@dataclass(frozen=True)
class Document:
    """Text extracted from one crawled page."""

    url: str
    title: str
    text: str


@dataclass(frozen=True)
class SearchIndex:
    """Inverted index plus page-level statistics."""

    inverted_index: InvertedIndex
    pages: dict[str, PageStats]

    def to_dict(self) -> dict[str, Any]:
        """Convert the index into a JSON-serialisable dictionary."""
        return {
            "inverted_index": self.inverted_index,
            "pages": self.pages,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SearchIndex:
        """Recreate a search index from a decoded JSON payload."""
        for key in ("inverted_index", "pages"):
            if key not in payload:
                raise IndexLoadError(f"missing key '{key}'")

        return cls(
            inverted_index=cast(InvertedIndex, payload["inverted_index"]),
            pages=cast(dict[str, PageStats], payload["pages"]),
        )


def tokenize(text: str) -> list[str]:
    """Return case-insensitive word tokens from text."""
    return TOKEN_PATTERN.findall(text.lower())


def build_index(documents: list[Document]) -> SearchIndex:
    """Build an inverted index in O(total terms) time."""
    inverted_index: InvertedIndex = {}
    pages: dict[str, PageStats] = {}

    for document in documents:
        tokens = tokenize(document.text)
        pages[document.url] = {
            "title": document.title,
            "total_terms": len(tokens),
            "unique_terms": len(set(tokens)),
        }

        for position, token in enumerate(tokens):
            postings = inverted_index.setdefault(token, {})
            posting = postings.setdefault(
                document.url,
                Posting(frequency=0, positions=[]),
            )
            posting["frequency"] += 1
            posting["positions"].append(position)

    return SearchIndex(inverted_index=inverted_index, pages=pages)


def save_index(search_index: SearchIndex, path: str | Path) -> None:
    """Save an index as deterministic, human-readable JSON."""
    index_path = Path(path)
    index_path.parent.mkdir(parents=True, exist_ok=True)

    with index_path.open("w", encoding="utf-8") as index_file:
        dump(search_index.to_dict(), index_file, indent=2, sort_keys=True)
        index_file.write("\n")


def load_index(path: str | Path) -> SearchIndex:
    """Load a search index from JSON."""
    try:
        with Path(path).open(encoding="utf-8") as index_file:
            payload = load(index_file)
    except JSONDecodeError as exc:
        raise IndexLoadError("invalid JSON") from exc

    if not isinstance(payload, dict):
        raise IndexLoadError("top-level JSON value must be an object")

    return SearchIndex.from_dict(payload)
