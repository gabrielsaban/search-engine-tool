from argparse import Namespace

import pytest

from benchmarks.search_benchmark import (
    QueryBenchmark,
    benchmark_summary,
    build_argument_parser,
    format_benchmark_report,
    generate_synthetic_documents,
    run_query_benchmarks,
    time_index_build,
    time_tokenisation,
)


def test_generate_synthetic_documents_is_deterministic() -> None:
    documents = generate_synthetic_documents(
        document_count=20,
        terms_per_document=12,
        vocabulary_size=8,
    )

    assert len(documents) == 20
    assert documents[0].url == "https://benchmark.local/page/1/"
    assert documents[4].text.split()[:5] == [
        "shared",
        "topic5",
        "doc5",
        "alpha",
        "beta",
    ]
    assert "rareterm17" in documents[16].text


@pytest.mark.parametrize(
    ("document_count", "terms_per_document", "vocabulary_size"),
    [(0, 8, 1), (1, 7, 1), (1, 8, 0)],
)
def test_generate_synthetic_documents_rejects_invalid_sizes(
    document_count: int,
    terms_per_document: int,
    vocabulary_size: int,
) -> None:
    with pytest.raises(ValueError):
        generate_synthetic_documents(
            document_count=document_count,
            terms_per_document=terms_per_document,
            vocabulary_size=vocabulary_size,
        )


def test_benchmark_summary_reports_index_shape() -> None:
    documents = generate_synthetic_documents(20, 12, 8)
    timed_index = time_index_build(documents)
    summary = benchmark_summary(timed_index.value)

    assert summary["documents"] == 20
    assert summary["unique_terms"] > 0
    assert summary["postings"] >= summary["unique_terms"]
    assert summary["positions"] == 20 * 12
    assert summary["index_json_bytes"] > 0


def test_query_benchmarks_return_counts_without_timing_assumptions() -> None:
    documents = generate_synthetic_documents(20, 12, 8)
    search_index = time_index_build(documents).value

    query_benchmarks = run_query_benchmarks(
        search_index,
        ['"alpha beta"', "rareterm17 shared", "missingterm"],
    )

    assert [benchmark.result_count for benchmark in query_benchmarks] == [4, 1, 0]
    assert all(benchmark.seconds >= 0 for benchmark in query_benchmarks)


def test_time_tokenisation_counts_tokens() -> None:
    documents = generate_synthetic_documents(3, 9, 4)

    timed_tokens = time_tokenisation(documents)

    assert timed_tokens.value == 27
    assert timed_tokens.seconds >= 0


def test_benchmark_parser_has_help_and_expected_defaults() -> None:
    parser = build_argument_parser()
    args = parser.parse_args([])

    assert "--source" in parser.format_help()
    assert isinstance(args, Namespace)
    assert args.source == "saved"
    assert args.documents == 500


def test_format_benchmark_report_includes_metrics_and_queries() -> None:
    report = format_benchmark_report(
        source_label="synthetic corpus",
        summary={
            "documents": 2,
            "unique_terms": 5,
            "postings": 6,
            "positions": 20,
            "index_json_bytes": 1000,
        },
        tokenisation_seconds=0.01,
        index_seconds=0.02,
        query_benchmarks=[
            QueryBenchmark(query="shared", result_count=2, seconds=0.003)
        ],
    )

    assert "Search Engine Benchmark" in report
    assert "  documents: 2" in report
    assert "  tokenisation_seconds: 0.010000" in report
    assert "  'shared': 2 result(s), 3.000 ms" in report
