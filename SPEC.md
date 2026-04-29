# Search Engine Specification

## Project Overview
- **Project Name**: SimpleSearch - Document Search Engine
- **Type**: Python CLI Application
- **Core Functionality**: A search engine that crawls documents, builds an inverted index, and ranks results using TF-IDF algorithm
- **Target Users**: Developers and users needing local document search capability

## Functionality Specification

### Core Features

#### 1. Document Processing
- **Tokenization**: Split text into words, handle punctuation
- **Text Preprocessing**:
  - Lowercase conversion
  - Stop word removal (common English words)
  - Stemming (Porter Stemmer)
  - Special character handling

#### 2. Inverted Index
- **Structure**: Dictionary mapping terms to document IDs with frequencies
- **Storage**: JSON file for persistence
- **Operations**:
  - Add document to index
  - Update index when documents change
  - Load/save index to disk

#### 3. Ranking Algorithm (TF-IDF)
- **Term Frequency (TF)**: Count of term in document / total terms
- **Inverse Document Frequency (IDF)**: log(total documents / documents containing term)
- **Score**: TF × IDF for each term, summed across query terms
- **Normalization**: Document length normalization

#### 4. Search Interface
- **CLI Commands**:
  - `index <path>` - Index documents from a directory
  - `search <query>` - Search indexed documents
  - `crawl <url>` - Crawl web pages
  - `stats` - Show index statistics
  - `clear` - Clear the index

#### 5. Bonus Features
- **Phrase Search**: Support for quoted phrases like `"exact phrase"`
- **Web Crawler**: Basic HTTP fetching with link extraction
- **Large Dataset Handling**: Efficient memory management with batch processing

### Data Flow
1. Documents → Tokenizer → Preprocessor → Inverted Index
2. Query → Tokenizer → Preprocessor → TF-IDF Calculator → Ranked Results

### Edge Cases
- Empty documents
- Duplicate documents
- No matching results
- Very long documents
- Special characters in text

## Acceptance Criteria
1. ✅ Can index multiple text files from a directory
2. ✅ Search returns relevant results ranked by TF-IDF
3. ✅ Phrase search works with quotes
4. ✅ Web crawler can fetch and index web pages
5. ✅ Index persists between sessions
6. ✅ CLI provides clear, formatted output
7. ✅ Handles 1000+ documents efficiently