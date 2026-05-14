# Crawler Design Notes

## Scope

The crawler targets `https://quotes.toscrape.com/` and follows the site's pagination links. This is enough to reach the quote listing pages needed for the coursework search index.

## Politeness

The crawler enforces a politeness delay before every request after the first request. The default delay is 6 seconds, matching the coursework requirement.

The sleep and clock functions are injectable. This lets automated tests verify politeness without making CI wait for real six-second sleeps.

## Extracted Text

For each quote card, the crawler extracts:

- Quote text.
- Author name.
- Tags.

These fields are combined into the document text so the index can support searches across quote content, authors, and tags.

If a page has no quote cards, the crawler falls back to the visible body text. This makes the parser more robust to simple HTML variations.

## Error Handling

Request failures and HTTP error responses are recorded as `CrawlError` entries rather than crashing the crawl. The caller receives both the successfully extracted documents and any crawl errors, which can be reported by the command-line interface later.

External pagination links are skipped and recorded as errors. This prevents the crawler from accidentally leaving the target site.

## Testing Strategy

Crawler tests use mocked HTTP responses, so they are fast and deterministic. The tests cover:

- Quote extraction.
- Fallback body extraction.
- Relative next-page URL resolution.
- Pagination crawling.
- The 6-second politeness delay.
- HTTP errors.
- Timeout errors.
- Page limits for development runs.
- External pagination links.
