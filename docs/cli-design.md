# CLI Design Notes

## Required Commands

The interactive shell supports the four coursework commands:

- `build`: crawl the target website, build the index, and save it.
- `load`: load a saved index from disk.
- `print <word>`: display the posting list for one word.
- `find <query terms>`: find pages containing all query terms.

It also supports `help`, `exit`, and `quit` for usability.

## State Management

The shell keeps the loaded `SearchIndex` in memory. Search commands require either `build` or `load` to run first, which avoids confusing errors from searching an absent index.

## Startup Options

The shell accepts optional arguments:

```text
--index-path data/index.json
--max-pages 1
--politeness-delay 0
```

The defaults are suitable for the coursework. The optional values are useful for development and short manual smoke tests.

For the final demonstration, the normal `build` command should use the required 6-second politeness delay. For quick local checks, `--max-pages 1 --politeness-delay 0` avoids waiting for a full crawl.

## Manual Smoke Test

Example short run:

```bash
printf 'build\nprint good\nfind good friends\nexit\n' | \
  PYTHONPATH=src python src/main.py \
  --index-path data/dev-smoke-index.json \
  --max-pages 1 \
  --politeness-delay 0
```

This exercises the real CLI entrypoint against the live first page only.

## Testing Strategy

Automated CLI tests inject fake crawler results, so they verify command behaviour without network access or real sleep delays. The tests cover command parsing, build, load, print, find, missing indexes, missing arguments, unknown commands, and startup options.
