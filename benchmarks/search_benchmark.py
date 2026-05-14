"""Reproducible benchmark runner for indexing and search."""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from json import dumps
from pathlib import Path
from time import perf_counter

from indexer import Document, SearchIndex, build_index, load_index, tokenize
from search import find_pages

DEFAULT_INDEX_PATH = Path("data/index.json")
DEFAULT_SAVED_QUERIES = (
    "good friends",
    '"good friends"',
    "indifference OR nonsense",
    "freinds",
)
DEFAULT_SYNTHETIC_QUERIES = (
    "shared topic7",
    '"alpha beta"',
    "rareterm17 shared",
    "missingterm",
)


@dataclass(frozen=True)
class TimedValue:
    """A value returned with elapsed seconds."""

    value: object
    seconds: float


@dataclass(frozen=True)
class QueryBenchmark:
    """Timing result for one search query."""

    query: str
    result_count: int
    seconds: float

    @property
    def milliseconds(self) -> float:
        return self.seconds * 1000


def generate_synthetic_documents(
    document_count: int,
    terms_per_document: int,
    vocabulary_size: int,
) -> list[Document]:
    """Generate deterministic documents for repeatable local benchmarks."""
    if document_count < 1:
        raise ValueError("document_count must be at least 1")
    if terms_per_document < 8:
        raise ValueError("terms_per_document must be at least 8")
    if vocabulary_size < 1:
        raise ValueError("vocabulary_size must be at least 1")

    vocabulary = [f"term{term_number:04d}" for term_number in range(vocabulary_size)]
    documents = []

    for document_number in range(1, document_count + 1):
        tokens = [
            "shared",
            f"topic{document_number % 10}",
            f"doc{document_number}",
        ]

        if document_number % 5 == 0:
            tokens.extend(["alpha", "beta"])
        if document_number % 17 == 0:
            tokens.append("rareterm17")

        vocabulary_cursor = document_number
        while len(tokens) < terms_per_document:
            tokens.append(vocabulary[vocabulary_cursor % vocabulary_size])
            vocabulary_cursor += 7

        documents.append(
            Document(
                url=f"https://benchmark.local/page/{document_number}/",
                title=f"Synthetic Page {document_number}",
                text=" ".join(tokens),
            )
        )

    return documents


def timed(
    operation: Callable[[], object],
    *,
    timer: Callable[[], float] = perf_counter,
) -> TimedValue:
    """Run an operation and return its result with elapsed seconds."""
    started_at = timer()
    value = operation()
    return TimedValue(value=value, seconds=timer() - started_at)


def time_tokenisation(
    documents: Iterable[Document],
    *,
    timer: Callable[[], float] = perf_counter,
) -> TimedValue:
    """Time tokenisation across a document iterable."""
    document_list = list(documents)
    return timed(
        lambda: sum(len(tokenize(document.text)) for document in document_list),
        timer=timer,
    )


def time_index_build(
    documents: Iterable[Document],
    *,
    timer: Callable[[], float] = perf_counter,
) -> TimedValue:
    """Time index construction over a document iterable."""
    document_list = list(documents)
    return timed(lambda: build_index(document_list), timer=timer)


def run_query_benchmarks(
    search_index: SearchIndex,
    queries: Iterable[str],
    *,
    timer: Callable[[], float] = perf_counter,
) -> list[QueryBenchmark]:
    """Time representative search queries without asserting specific timings."""
    query_benchmarks = []

    for query in queries:
        timed_result = timed(
            lambda query=query: find_pages(search_index, query), timer=timer
        )
        query_benchmarks.append(
            QueryBenchmark(
                query=query,
                result_count=len(timed_result.value),
                seconds=timed_result.seconds,
            )
        )

    return query_benchmarks


def index_json_size_bytes(search_index: SearchIndex) -> int:
    """Return deterministic JSON byte size for an index payload."""
    payload = dumps(search_index.to_dict(), sort_keys=True, separators=(",", ":"))
    return len(payload.encode("utf-8"))


def benchmark_summary(search_index: SearchIndex) -> dict[str, int]:
    """Return structural metrics useful for complexity discussion."""
    posting_count = sum(
        len(postings) for postings in search_index.inverted_index.values()
    )
    position_count = sum(
        len(posting["positions"])
        for postings in search_index.inverted_index.values()
        for posting in postings.values()
    )
    return {
        "documents": len(search_index.pages),
        "unique_terms": len(search_index.inverted_index),
        "postings": posting_count,
        "positions": position_count,
        "index_json_bytes": index_json_size_bytes(search_index),
    }


def build_argument_parser() -> ArgumentParser:
    """Build the benchmark command-line parser."""
    parser = ArgumentParser(description="Benchmark indexing and search operations.")
    parser.add_argument(
        "--source",
        choices=("saved", "synthetic"),
        default="saved",
        help="Load the committed index or build a deterministic synthetic corpus.",
    )
    parser.add_argument(
        "--index-path",
        type=Path,
        default=DEFAULT_INDEX_PATH,
        help="Saved index path used when --source saved is selected.",
    )
    parser.add_argument(
        "--documents",
        type=int,
        default=500,
        help="Synthetic document count.",
    )
    parser.add_argument(
        "--terms-per-document",
        type=int,
        default=120,
        help="Synthetic terms per document.",
    )
    parser.add_argument(
        "--vocabulary-size",
        type=int,
        default=1000,
        help="Synthetic vocabulary size.",
    )
    parser.add_argument(
        "--query",
        action="append",
        dest="queries",
        help="Query to benchmark. Can be provided multiple times.",
    )
    return parser


def run_benchmark(args: Namespace) -> list[str]:
    """Run a benchmark from parsed command-line arguments."""
    if args.source == "saved":
        timed_index = timed(lambda: load_index(args.index_path))
        search_index = timed_index.value
        tokenisation = None
        index_build = timed_index
        queries = args.queries or DEFAULT_SAVED_QUERIES
        source_label = f"saved index: {args.index_path}"
    else:
        documents = generate_synthetic_documents(
            args.documents,
            args.terms_per_document,
            args.vocabulary_size,
        )
        tokenisation = time_tokenisation(documents)
        index_build = time_index_build(documents)
        search_index = index_build.value
        queries = args.queries or DEFAULT_SYNTHETIC_QUERIES
        source_label = (
            f"synthetic corpus: {args.documents} documents, "
            f"{args.terms_per_document} terms/document, "
            f"{args.vocabulary_size} vocabulary terms"
        )

    summary = benchmark_summary(search_index)
    query_benchmarks = run_query_benchmarks(search_index, queries)

    return format_benchmark_report(
        source_label=source_label,
        summary=summary,
        tokenisation_seconds=tokenisation.seconds if tokenisation else None,
        index_seconds=index_build.seconds,
        query_benchmarks=query_benchmarks,
    )


def format_benchmark_report(
    *,
    source_label: str,
    summary: dict[str, int],
    tokenisation_seconds: float | None,
    index_seconds: float,
    query_benchmarks: list[QueryBenchmark],
) -> list[str]:
    """Format a benchmark report for terminal output."""
    lines = [
        "Search Engine Benchmark",
        f"Source: {source_label}",
        "",
        "Index metrics:",
        f"  documents: {summary['documents']}",
        f"  unique_terms: {summary['unique_terms']}",
        f"  postings: {summary['postings']}",
        f"  positions: {summary['positions']}",
        f"  index_json_bytes: {summary['index_json_bytes']}",
        "",
        "Timings:",
    ]

    if tokenisation_seconds is not None:
        lines.append(f"  tokenisation_seconds: {tokenisation_seconds:.6f}")

    lines.append(f"  index_or_load_seconds: {index_seconds:.6f}")
    lines.extend(["", "Query timings:"])

    for query_benchmark in query_benchmarks:
        lines.append(
            f"  {query_benchmark.query!r}: "
            f"{query_benchmark.result_count} result(s), "
            f"{query_benchmark.milliseconds:.3f} ms"
        )

    return lines


def main() -> None:
    """Run the benchmark script."""
    parser = build_argument_parser()
    for line in run_benchmark(parser.parse_args()):
        print(line)


if __name__ == "__main__":
    main()
