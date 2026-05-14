"""Command-line shell for the search engine coursework tool."""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from src.crawler import CrawlConfig, CrawlResult, crawl_site
from src.indexer import IndexLoadError, SearchIndex, build_index, load_index, save_index
from src.search import (
    explain_query,
    find_pages,
    format_postings,
    format_search_explanation,
    format_search_results,
    suggest_terms,
)

DEFAULT_INDEX_PATH = Path("data/index.json")


def parse_command(raw_command: str) -> tuple[str, str]:
    """Split a shell input line into command name and argument text."""
    stripped_command = raw_command.strip()
    if not stripped_command:
        return "", ""

    command, _, arguments = stripped_command.partition(" ")
    return command.lower(), arguments.strip()


@dataclass
class SearchShell:
    """Stateful command dispatcher for the interactive shell."""

    index_path: Path = DEFAULT_INDEX_PATH
    crawler: Callable[[], CrawlResult] = lambda: crawl_site(CrawlConfig())
    search_index: SearchIndex | None = None

    def execute(self, raw_command: str) -> list[str]:
        """Execute one shell command and return lines to display."""
        command, arguments = parse_command(raw_command)

        if command == "":
            return []
        if command == "build":
            return self._build()
        if command == "load":
            return self._load()
        if command == "print":
            return self._print(arguments)
        if command == "find":
            return self._find(arguments)
        if command == "explain":
            return self._explain(arguments)
        if command == "help":
            return self._help()
        if command in {"exit", "quit"}:
            return ["Goodbye."]

        return [f"Unknown command '{command}'. Type 'help' for available commands."]

    def should_exit(self, raw_command: str) -> bool:
        """Return whether a raw command should close the shell."""
        command, _arguments = parse_command(raw_command)
        return command in {"exit", "quit"}

    def _build(self) -> list[str]:
        crawl_result = self.crawler()
        lines = [f"Crawled {len(crawl_result.documents)} page(s)."]

        for error in crawl_result.errors:
            lines.append(f"Warning: {error.url} - {error.message}")

        if not crawl_result.documents:
            lines.append("No documents were crawled; index was not updated.")
            return lines

        self.search_index = build_index(crawl_result.documents)
        save_index(self.search_index, self.index_path)
        lines.append(
            f"Indexed {len(self.search_index.inverted_index)} unique term(s) "
            f"and saved to {self.index_path}."
        )
        return lines

    def _load(self) -> list[str]:
        if not self.index_path.exists():
            return [f"No index file found at {self.index_path}."]

        try:
            self.search_index = load_index(self.index_path)
        except IndexLoadError as exc:
            return [f"Could not load index from {self.index_path}: {exc}."]

        return [
            f"Loaded index from {self.index_path}.",
            f"Index contains {len(self.search_index.inverted_index)} unique term(s) "
            f"across {len(self.search_index.pages)} page(s).",
        ]

    def _print(self, arguments: str) -> list[str]:
        if not arguments:
            return ["Usage: print <word>"]
        if self.search_index is None:
            return ["No index loaded. Run 'build' or 'load' first."]

        return format_postings(self.search_index, arguments)

    def _find(self, arguments: str) -> list[str]:
        if not arguments:
            return ["Usage: find <query terms>"]
        if self.search_index is None:
            return ["No index loaded. Run 'build' or 'load' first."]

        results = find_pages(self.search_index, arguments)
        lines = format_search_results(results)

        if not results:
            suggestions = suggest_terms(self.search_index, arguments)
            if suggestions:
                lines.append(f"Did you mean: {', '.join(suggestions)}?")

        return lines

    def _explain(self, arguments: str) -> list[str]:
        if not arguments:
            return ["Usage: explain <query terms>"]
        if self.search_index is None:
            return ["No index loaded. Run 'build' or 'load' first."]

        explanation = explain_query(self.search_index, arguments)
        lines = format_search_explanation(explanation)

        if explanation is None:
            suggestions = suggest_terms(self.search_index, arguments)
            if suggestions:
                lines.append(f"Did you mean: {', '.join(suggestions)}?")

        return lines

    def _help(self) -> list[str]:
        return [
            "Available commands:",
            "  build             Crawl the target site, build the index, and save it.",
            "  load              Load the saved index from disk.",
            "  print <word>      Print the posting list for a word.",
            "  find <query>      Find pages containing all query terms.",
            '                    Supports phrases like "good friends" and OR.',
            "  explain <query>   Explain the top result's score.",
            "  help              Show this help text.",
            "  exit              Leave the shell.",
        ]


def build_argument_parser() -> ArgumentParser:
    """Build the command-line argument parser for shell startup options."""
    parser = ArgumentParser(description="Search Engine Tool interactive shell")
    parser.add_argument(
        "--index-path",
        type=Path,
        default=DEFAULT_INDEX_PATH,
        help="Path used by build/load for the saved index.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Optional crawl page limit for development or short demos.",
    )
    parser.add_argument(
        "--politeness-delay",
        type=float,
        default=CrawlConfig.politeness_delay,
        help="Delay in seconds between live requests.",
    )
    return parser


def create_shell(args: Namespace) -> SearchShell:
    """Create a shell from parsed startup options."""
    crawl_config = CrawlConfig(
        max_pages=args.max_pages,
        politeness_delay=args.politeness_delay,
    )
    return SearchShell(
        index_path=args.index_path,
        crawler=lambda: crawl_site(crawl_config),
    )


def main() -> None:
    """Run the interactive search shell."""
    shell = create_shell(build_argument_parser().parse_args())
    print("Search Engine Tool")
    print("Type 'help' for commands.")

    while True:
        try:
            raw_command = input("> ")
        except EOFError:
            print()
            break

        output_lines = shell.execute(raw_command)
        for line in output_lines:
            print(line)

        if shell.should_exit(raw_command):
            break


if __name__ == "__main__":
    main()
