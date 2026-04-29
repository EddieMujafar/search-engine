# SimpleSearch - Document Search Engine

A Python-based search engine that crawls, indexes, and ranks documents using TF-IDF algorithm.

## Features

- **Tokenization & Preprocessing**: Lowercase conversion, stop word removal, stemming
- **Inverted Index**: Fast term-based document lookup
- **TF-IDF Ranking**: Relevance scoring based on term frequency and inverse document frequency
- **Phrase Search**: Use quotes for exact phrase matching
- **Web Crawler**: Crawl and index web pages
- **CLI Interface**: Interactive command-line search

## Installation

```bash
pip install requests
```

## Usage

### Interactive Mode

```bash
python search_engine.py
```

### Command-Line Mode

```bash
# Index a directory
python search_engine.py index ./documents

# Search documents
python search_engine.py search "machine learning"

# Crawl web pages
python search_engine.py crawl https://example.com

# Show statistics
python search_engine.py stats

# Clear index
python search_engine.py clear
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `index <dir>` | Index all text files in a directory |
| `search <query>` | Search indexed documents |
| `crawl <url>` | Crawl web pages starting from a URL |
| `stats` | Show index statistics |
| `clear` | Clear the index |
| `help` | Show help message |
| `exit` | Exit the program |

## Search Tips

- Use quotes for exact phrase: `"artificial intelligence"`
- Longer, more specific queries yield better results
- Results are ranked by TF-IDF relevance score

## Ranking Logic

The search engine uses **TF-IDF (Term Frequency - Inverse Document Frequency)** for ranking:

1. **Term Frequency (TF)**: Measures how often a term appears in a document
   - `TF = term_count / total_terms_in_document`

2. **Inverse Document Frequency (IDF)**: Measures how unique a term is across all documents
   - `IDF = log(total_documents / documents_containing_term)`

3. **Final Score**: `TF × IDF` for each query term, summed across all terms

## Project Structure

```
search-engine/
├── search_engine.py   # Main search engine implementation
├── SPEC.md           # Project specification
├── README.md         # This file
└── sample_docs/      # Sample documents for testing
```

## License

MIT