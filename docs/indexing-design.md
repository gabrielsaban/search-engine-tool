# Indexing Design Notes

## Tokenisation

The indexer treats search as case-insensitive, matching the coursework brief. Text is lowercased before token extraction.

Current token rules:

- Words and numbers are indexed.
- Apostrophes inside words are preserved, so `that's` remains one token.
- Hyphenated text is split into separate terms.
- Surrounding punctuation is ignored.
- Blank text produces no tokens.

These rules keep the implementation explainable while handling the quote website's common punctuation patterns.

## Inverted Index Shape

The index maps each word to each page where that word appears:

```python
{
    "good": {
        "https://quotes.toscrape.com/page/1/": {
            "frequency": 2,
            "positions": [0, 3],
        }
    }
}
```

This supports the required `print <word>` command directly because the posting list for a term can be retrieved in one dictionary lookup.

## Page Statistics

Page-level statistics are stored separately from the term postings:

```python
{
    "https://quotes.toscrape.com/page/1/": {
        "title": "Quotes Page 1",
        "total_terms": 5,
        "unique_terms": 4,
    }
}
```

Keeping page metadata separate avoids duplicating page information inside every posting.

## Complexity

Building the index is `O(total_terms)` because each token is processed once. Looking up a single term is `O(1)` on average for the dictionary lookup, plus `O(number_of_matching_pages)` to display or process its posting list.

The saved JSON is deterministic through sorted keys, making generated index files easier to inspect, compare, and submit.
