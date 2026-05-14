"""Build and persist an inverted index for crawled web pages."""

from __future__ import annotations

import re
from dataclasses import dataclass

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
