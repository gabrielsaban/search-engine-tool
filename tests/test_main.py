from pathlib import Path

from src import main
from src.crawler import CrawlError, CrawlResult
from src.indexer import Document
from src.main import SearchShell, build_argument_parser, create_shell, parse_command


def test_parse_command_splits_command_and_arguments() -> None:
    assert parse_command("find good friends") == ("find", "good friends")
    assert parse_command("  LOAD  ") == ("load", "")
    assert parse_command("") == ("", "")


def test_load_reports_missing_index(tmp_path) -> None:
    shell = SearchShell(index_path=tmp_path / "missing.json")

    assert shell.execute("load") == [
        f"No index file found at {tmp_path / 'missing.json'}."
    ]


def test_load_reports_corrupt_index_json(tmp_path) -> None:
    index_path = tmp_path / "index.json"
    index_path.write_text("{not valid json", encoding="utf-8")
    shell = SearchShell(index_path=index_path)

    assert shell.execute("load") == [
        f"Could not load index from {index_path}: invalid JSON."
    ]


def test_load_reports_invalid_index_structure(tmp_path) -> None:
    index_path = tmp_path / "index.json"
    index_path.write_text('{"inverted_index": {}}', encoding="utf-8")
    shell = SearchShell(index_path=index_path)

    assert shell.execute("load") == [
        f"Could not load index from {index_path}: missing key 'pages'."
    ]


def test_build_crawls_indexes_and_saves(tmp_path) -> None:
    index_path = tmp_path / "index.json"

    def fake_crawler():
        return CrawlResult(
            documents=[
                Document(
                    url="https://quotes.toscrape.com/",
                    title="Quotes to Scrape",
                    text="Good friends and good books.",
                )
            ],
            errors=[],
            visited_urls=("https://quotes.toscrape.com/",),
        )

    shell = SearchShell(index_path=index_path, crawler=fake_crawler)

    assert shell.execute("build") == [
        "Crawled 1 page(s).",
        f"Indexed 4 unique term(s) and saved to {index_path}.",
    ]
    assert index_path.exists()


def test_load_print_and_find_commands(tmp_path) -> None:
    index_path = tmp_path / "index.json"

    def fake_crawler():
        return CrawlResult(
            documents=[
                Document(
                    url="https://quotes.toscrape.com/",
                    title="Quotes to Scrape",
                    text="Good friends and good books.",
                )
            ],
            errors=[],
            visited_urls=("https://quotes.toscrape.com/",),
        )

    shell = SearchShell(index_path=index_path, crawler=fake_crawler)
    shell.execute("build")
    shell.search_index = None

    assert shell.execute("load") == [
        f"Loaded index from {index_path}.",
        "Index contains 4 unique term(s) across 1 page(s).",
    ]
    assert shell.execute("print good") == [
        "good",
        "https://quotes.toscrape.com/ | frequency=2 | positions=[0, 3]",
    ]
    assert shell.execute("find good friends") == [
        "1. Quotes to Scrape | score=3.0000 | "
        "terms=good:2, friends:1 | https://quotes.toscrape.com/"
    ]
    assert shell.execute("find freinds") == [
        "No matching pages found.",
        "Did you mean: friends?",
    ]


def test_search_commands_require_loaded_index(tmp_path) -> None:
    shell = SearchShell(index_path=tmp_path / "index.json")

    assert shell.execute("print good") == [
        "No index loaded. Run 'build' or 'load' first."
    ]
    assert shell.execute("find good") == [
        "No index loaded. Run 'build' or 'load' first."
    ]


def test_command_validation_and_help(tmp_path) -> None:
    shell = SearchShell(index_path=tmp_path / "index.json")

    assert shell.execute("") == []
    assert shell.execute("exit") == ["Goodbye."]
    assert shell.should_exit("quit")
    assert not shell.should_exit("help")
    assert shell.execute("print") == ["Usage: print <word>"]
    assert shell.execute("find") == ["Usage: find <query terms>"]
    assert shell.execute("unknown") == [
        "Unknown command 'unknown'. Type 'help' for available commands."
    ]
    assert shell.execute("help")[0] == "Available commands:"


def test_build_reports_crawl_errors(tmp_path) -> None:
    index_path = tmp_path / "index.json"

    def fake_crawler():
        return CrawlResult(
            documents=[],
            errors=[
                CrawlError(
                    url="https://quotes.toscrape.com/",
                    message="500 Server Error",
                )
            ],
            visited_urls=(),
        )

    shell = SearchShell(index_path=index_path, crawler=fake_crawler)

    assert shell.execute("build") == [
        "Crawled 0 page(s).",
        "Warning: https://quotes.toscrape.com/ - 500 Server Error",
        "No documents were crawled; index was not updated.",
    ]
    assert not Path(index_path).exists()


def test_create_shell_uses_startup_options(tmp_path) -> None:
    args = build_argument_parser().parse_args(
        [
            "--index-path",
            str(tmp_path / "custom.json"),
            "--max-pages",
            "1",
            "--politeness-delay",
            "0",
        ]
    )

    shell = create_shell(args)

    assert shell.index_path == tmp_path / "custom.json"


def test_main_loop_prints_output_and_exits(monkeypatch, capsys) -> None:
    commands = iter(["help", "exit"])

    monkeypatch.setattr("builtins.input", lambda _prompt: next(commands))
    monkeypatch.setattr("sys.argv", ["main.py"])

    main.main()

    output = capsys.readouterr().out
    assert "Search Engine Tool" in output
    assert "Available commands:" in output
    assert "Goodbye." in output


def test_main_loop_handles_eof(monkeypatch, capsys) -> None:
    def raise_eof(_prompt: str) -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)
    monkeypatch.setattr("sys.argv", ["main.py"])

    main.main()

    assert "Search Engine Tool" in capsys.readouterr().out
