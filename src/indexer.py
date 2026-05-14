"""Build and persist an inverted index for crawled web pages."""

from __future__ import annotations

import re
from dataclasses import dataclass
from json import dump, load
from pathlib import Path
from typing import Any

TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")


@dataclass(frozen=True)
class Document:
    """Text extracted from one crawled page."""

    url: str
    title: str
    text: str


@dataclass(frozen=True)
class SearchIndex:
    """Inverted index plus page-level statistics."""

    inverted_index: dict[str, dict[str, dict[str, list[int] | int]]]
    pages: dict[str, dict[str, int | str]]

    def to_dict(self) -> dict[str, Any]:
        """Convert the index into a JSON-serialisable dictionary."""
        return {
            "inverted_index": self.inverted_index,
            "pages": self.pages,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SearchIndex:
        """Recreate a search index from a decoded JSON payload."""
        return cls(
            inverted_index=payload["inverted_index"],
            pages=payload["pages"],
        )


def tokenize(text: str) -> list[str]:
    """Return case-insensitive word tokens from text."""
    return TOKEN_PATTERN.findall(text.lower())


def build_index(documents: list[Document]) -> SearchIndex:
    """Build an inverted index in O(total terms) time."""
    inverted_index: dict[str, dict[str, dict[str, list[int] | int]]] = {}
    pages: dict[str, dict[str, int | str]] = {}

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
                {
                    "frequency": 0,
                    "positions": [],
                },
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
    with Path(path).open(encoding="utf-8") as index_file:
        payload = load(index_file)

    return SearchIndex.from_dict(payload)
