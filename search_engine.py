"""
SimpleSearch - A document search engine with crawling, indexing, and TF-IDF ranking.
"""

import os
import re
import json
import math
import hashlib
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path
import heapq
import time
from urllib.parse import urlparse, urljoin
import requests
from html import unescape
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


# ============== Configuration ==============
class Config:
    """Search engine configuration."""
    INDEX_DB = "search_index.db"
    STOP_WORDS = frozenset({
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'or', 'that',
        'the', 'to', 'was', 'were', 'will', 'with', 'this', 'but', 'they',
        'have', 'had', 'what', 'when', 'where', 'who', 'which', 'why', 'how',
        'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other',
        'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
        'than', 'too', 'very', 'can', 'just', 'should', 'now', 'also'
    })
    MAX_CRAWL_PAGES = 50
    CRAWL_TIMEOUT = 10
    MIN_WORD_LENGTH = 2
    MAX_DOC_LENGTH = 100000


# ============== Data Structures ==============
@dataclass
class Document:
    """Represents a document in the index."""
    doc_id: int
    path: str
    title: str
    content: str
    word_count: int
    indexed_at: float
    
    def to_dict(self):
        return asdict(self)


@dataclass
class SearchResult:
    """Represents a search result."""
    doc_id: int
    path: str
    title: str
    snippet: str
    score: float
    
    def to_dict(self):
        return asdict(self)


# ============== Stemmer (Porter Stemmer simplified) ==============
class SimpleStemmer:
    """A simplified Porter stemmer for basic word stemming."""
    
    def __init__(self):
        self._suffixes = [
            ('ational', 'ate'), ('tional', 'tion'), ('enci', 'ence'),
            ('anci', 'ance'), ('izer', 'ize'), ('isation', 'ize'),
            ('ization', 'ize'), ('ation', 'ate'), ('ator', 'ate'),
            ('alism', 'al'), ('iveness', 'ive'), ('fulness', 'ful'),
            ('ousness', 'ous'), ('aliti', 'al'), ('iviti', 'ive'),
            ('biliti', 'ble'), ('alli', 'al'), ('entli', 'ent'),
            ('eli', 'e'), ('ous', 'ous'), ('ing', ''),
            ('ement', ''), ('ment', ''), ('ent', ''),
            ('ness', ''), ('ful', ''), ('less', ''),
            ('able', ''), ('ible', ''), ('al', ''),
            ('ive', ''), ('ous', ''), ('ant', ''),
            ('ence', ''), ('ance', ''), ('er', ''), ('ic', ''),
        ]
    
    def stem(self, word: str) -> str:
        """Stem a word to its root form."""
        if len(word) <= 3:
            return word
        
        word = word.lower()
        for suffix, replacement in self._suffixes:
            if word.endswith(suffix) and len(word) - len(suffix) + len(replacement) >= 3:
                word = word[:-len(suffix)] + replacement
                break
        
        return word


# ============== Text Preprocessor ==============
class TextPreprocessor:
    """Handles tokenization and text preprocessing."""
    
    def __init__(self):
        self.stemmer = SimpleStemmer()
        self.stop_words = Config.STOP_WORDS
    
    def tokenize(self, text: str) -> List[str]:
        """Convert text into tokens."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Remove URLs
        text = re.sub(r'https?://\S+', ' ', text)
        # Remove email addresses
        text = re.sub(r'\S+@\S+', ' ', text)
        # Keep alphanumeric and spaces
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        # Split into words
        words = text.lower().split()
        return words
    
    def preprocess(self, text: str) -> List[str]:
        """Preprocess text: tokenize, remove stop words, stem."""
        tokens = self.tokenize(text)
        
        # Filter tokens
        processed = []
        for token in tokens:
            # Skip short words and stop words
            if len(token) < Config.MIN_WORD_LENGTH:
                continue
            if token in self.stop_words:
                continue
            # Skip pure numbers
            if token.isdigit():
                continue
            # Stem the word
            stemmed = self.stemmer.stem(token)
            if len(stemmed) >= Config.MIN_WORD_LENGTH:
                processed.append(stemmed)
        
        return processed
    
    def extract_phrases(self, text: str) -> List[str]:
        """Extract quoted phrases from text."""
        # Support both double and single quotes
        phrases = re.findall(r'"([^"]+)"', text)
        if not phrases:
            phrases = re.findall(r"'([^']+)'", text)
        return phrases


# ============== Inverted Index ==============
class InvertedIndex:
    """Inverted index for fast document search."""
    
    def __init__(self):
        self.term_doc_freq: Dict[str, Dict[int, int]] = defaultdict(dict)
        self.doc_term_freq: Dict[int, Dict[str, int]] = {}
        self.doc_lengths: Dict[int, int] = {}
        self.documents: Dict[int, Document] = {}
        self.doc_count = 0
        self._lock = threading.Lock()
    
    def add_document(self, doc: Document) -> None:
        """Add a document to the index."""
        with self._lock:
            # Store document
            self.documents[doc.doc_id] = doc
            
            # Build term frequencies for this document
            preprocessor = TextPreprocessor()
            terms = preprocessor.preprocess(doc.content)
            
            term_freq = defaultdict(int)
            for term in terms:
                term_freq[term] += 1
            
            # Store term frequencies
            self.doc_term_freq[doc.doc_id] = dict(term_freq)
            self.doc_lengths[doc.doc_id] = len(terms)
            
            # Update inverted index
            for term, freq in term_freq.items():
                if doc.doc_id not in self.term_doc_freq[term]:
                    self.term_doc_freq[term][doc.doc_id] = freq
                else:
                    self.term_doc_freq[term][doc.doc_id] += freq
            
            self.doc_count += 1
    
    def get_term_frequency(self, term: str, doc_id: int) -> int:
        """Get frequency of a term in a document."""
        preprocessor = TextPreprocessor()
        stemmed = preprocessor.stemmer.stem(term.lower())
        return self.doc_term_freq.get(doc_id, {}).get(stemmed, 0)
    
    def get_document_frequency(self, term: str) -> int:
        """Get number of documents containing a term."""
        preprocessor = TextPreprocessor()
        stemmed = preprocessor.stemmer.stem(term.lower())
        return len(self.term_doc_freq.get(stemmed, {}))
    
    def get_documents_with_term(self, term: str) -> Dict[int, int]:
        """Get all documents containing a term with their frequencies."""
        preprocessor = TextPreprocessor()
        stemmed = preprocessor.stemmer.stem(term.lower())
        raw = self.term_doc_freq.get(stemmed, {})
        # Convert string keys to integers
        return {int(k): v for k, v in raw.items()}
    
    def get_total_documents(self) -> int:
        """Get total number of indexed documents."""
        return self.doc_count
    
    def clear(self) -> None:
        """Clear the entire index."""
        with self._lock:
            self.term_doc_freq.clear()
            self.doc_term_freq.clear()
            self.doc_lengths.clear()
            self.documents.clear()
            self.doc_count = 0
    
    def save(self, filepath: str) -> None:
        """Save index to file."""
        data = {
            'term_doc_freq': {k: dict(v) for k, v in self.term_doc_freq.items()},
            'doc_term_freq': {str(k): v for k, v in self.doc_term_freq.items()},
            'doc_lengths': self.doc_lengths,
            'documents': {k: v.to_dict() for k, v in self.documents.items()},
            'doc_count': self.doc_count
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    
    def load(self, filepath: str) -> None:
        """Load index from file."""
        if not os.path.exists(filepath):
            return
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.term_doc_freq = defaultdict(dict, {k: v for k, v in data.get('term_doc_freq', {}).items()})
        self.doc_term_freq = {int(k): v for k, v in data.get('doc_term_freq', {}).items()}
        self.doc_lengths = data.get('doc_lengths', {})
        self.documents = {int(k): Document(**v) for k, v in data.get('documents', {}).items()}
        self.doc_count = data.get('doc_count', 0)


# ============== TF-IDF Ranker ==============
class TFIDFRanker:
    """TF-IDF based document ranker."""
    
    def __init__(self, index: InvertedIndex):
        self.index = index
    
    def compute_tf(self, term: str, doc_id: int) -> float:
        """Compute term frequency (normalized)."""
        term_freq = self.index.get_term_frequency(term, doc_id)
        doc_length = self.index.doc_lengths.get(doc_id, 1)
        if doc_length == 0:
            return 0
        return term_freq / doc_length
    
    def compute_idf(self, term: str) -> float:
        """Compute inverse document frequency."""
        N = self.index.get_total_documents()
        if N == 0:
            return 0
        
        df = self.index.get_document_frequency(term)
        if df == 0:
            return 0
        
        return math.log(N / df)
    
    def compute_tfidf(self, term: str, doc_id: int) -> float:
        """Compute TF-IDF score for a term in a document."""
        tf = self.compute_tf(term, doc_id)
        idf = self.compute_idf(term)
        return tf * idf
    
    def rank_documents(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Rank documents based on query using TF-IDF."""
        preprocessor = TextPreprocessor()
        
        # Extract phrases for phrase search
        phrases = preprocessor.extract_phrases(query)
        
        # Get query terms (excluding phrases)
        query_without_phrases = re.sub(r'"[^"]+"', '', query)
        query_terms = preprocessor.preprocess(query_without_phrases)
        
        # Add phrase terms
        for phrase in phrases:
            phrase_terms = preprocessor.preprocess(phrase)
            query_terms.extend(phrase_terms)
        
        if not query_terms:
            return []
        
        # Score all documents
        doc_scores: Dict[int, float] = defaultdict(float)
        
        for term in query_terms:
            # Get documents containing this term
            term_docs = self.index.get_documents_with_term(term)
            
            for doc_id, freq in term_docs.items():
                tfidf = self.compute_tfidf(term, doc_id)
                doc_scores[doc_id] += tfidf
        
        for term in query_terms:
            # Get documents containing this term
            term_docs = self.index.get_documents_with_term(term)
            
            for doc_id, freq in term_docs.items():
                tfidf = self.compute_tfidf(term, doc_id)
                doc_scores[doc_id] += tfidf
        
        # Apply phrase bonus
        for phrase in phrases:
            phrase_terms = preprocessor.preprocess(phrase)
            if phrase_terms:
                for doc_id, doc in self.index.documents.items():
                    content_lower = doc.content.lower()
                    if phrase.lower() in content_lower:
                        doc_scores[doc_id] += 0.5  # Bonus for phrase match
        
        # Get top documents
        top_docs = heapq.nlargest(limit, doc_scores.items(), key=lambda x: x[1])
        
        results = []
        for doc_id, score in top_docs:
            doc = self.index.documents.get(doc_id)
            if doc:
                # Create snippet
                snippet = self._create_snippet(doc.content, query_terms[:3])
                results.append(SearchResult(
                    doc_id=doc_id,
                    path=doc.path,
                    title=doc.title,
                    snippet=snippet,
                    score=score
                ))
        
        return results
    
    def _create_snippet(self, content: str, terms: List[str], context: int = 50) -> str:
        """Create a snippet around the first matching term."""
        content_lower = content.lower()
        
        for term in terms:
            pos = content_lower.find(term)
            if pos != -1:
                start = max(0, pos - context)
                end = min(len(content), pos + len(term) + context)
                snippet = content[start:end].strip()
                
                if start > 0:
                    snippet = "..." + snippet
                if end < len(content):
                    snippet = snippet + "..."
                
                return snippet
        
        # Return beginning if no term found
        return content[:context * 2] + "..." if len(content) > context * 2 else content


# ============== Web Crawler ==============
class WebCrawler:
    """Basic web crawler for fetching web pages."""
    
    def __init__(self, max_pages: int = Config.MAX_CRAWL_PAGES):
        self.max_pages = max_pages
        self.visited: Set[str] = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SimpleSearch/1.0 (Document Search Engine)'
        })
    
    def fetch(self, url: str) -> Optional[Tuple[str, str]]:
        """Fetch a web page and return (title, content)."""
        if url in self.visited:
            return None
        
        self.visited.add(url)
        
        try:
            response = self.session.get(url, timeout=Config.CRAWL_TIMEOUT)
            response.raise_for_status()
            
            html = response.text
            
            # Extract title
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
            title = title_match.group(1) if title_match else url
            
            # Remove HTML tags
            text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = unescape(text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Limit content length
            if len(text) > Config.MAX_DOC_LENGTH:
                text = text[:Config.MAX_DOC_LENGTH]
            
            return title, text
            
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_links(self, base_url: str, html: str) -> List[str]:
        """Extract links from HTML."""
        links = []
        
        # Find all anchor tags
        for match in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\']', html, re.IGNORECASE):
            href = match.group(1)
            
            # Resolve relative URLs
            if not href.startswith(('http://', 'https://')):
                href = urljoin(base_url, href)
            
            # Only keep http/https links
            if href.startswith(('http://', 'https://')):
                links.append(href)
        
        return list(set(links))[:10]  # Limit to 10 unique links
    
    def crawl(self, start_url: str, index, progress_callback=None) -> int:
        """Crawl web pages starting from a URL."""
        urls_to_visit = [start_url]
        crawled_count = 0
        doc_id = index.doc_count
        
        while urls_to_visit and crawled_count < self.max_pages:
            url = urls_to_visit.pop(0)
            
            if url in self.visited:
                continue
            
            result = self.fetch(url)
            if result:
                title, content = result
                
                # Create document
                doc = Document(
                    doc_id=doc_id,
                    path=url,
                    title=title,
                    content=content,
                    word_count=len(content.split()),
                    indexed_at=time.time()
                )
                
                index.add_document(doc)
                doc_id += 1
                crawled_count += 1
                
                if progress_callback:
                    progress_callback(crawled_count, url)
                
                # Extract and add new links
                links = self.extract_links(url, content)
                for link in links:
                    if link not in self.visited and len(urls_to_visit) < 100:
                        urls_to_visit.append(link)
        
        return crawled_count


# ============== Search Engine ==============
class SearchEngine:
    """Main search engine class."""
    
    def __init__(self, index_path: str = "search_index.json"):
        self.index = InvertedIndex()
        self.index_path = index_path
        self.ranker = TFIDFRanker(self.index)
        self._load_index()
    
    def _load_index(self):
        """Load existing index if available."""
        if os.path.exists(self.index_path):
            try:
                self.index.load(self.index_path)
                print(f"Loaded index with {self.index.get_total_documents()} documents")
            except Exception as e:
                print(f"Warning: Could not load index: {e}")
    
    def _save_index(self):
        """Save index to disk."""
        try:
            self.index.save(self.index_path)
        except Exception as e:
            print(f"Error saving index: {e}")
    
    def index_directory(self, dir_path: str, extensions: List[str] = ['.txt', '.md', '.html']) -> int:
        """Index all documents in a directory."""
        if not os.path.exists(dir_path):
            print(f"Directory not found: {dir_path}")
            return 0
        
        doc_id = self.index.doc_count
        files_found = []
        
        # Find all matching files
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    files_found.append(os.path.join(root, file))
        
        print(f"Found {len(files_found)} files to index...")
        
        # Index files
        for i, filepath in enumerate(files_found):
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                if not content.strip():
                    continue
                
                # Limit content length
                if len(content) > Config.MAX_DOC_LENGTH:
                    content = content[:Config.MAX_DOC_LENGTH]
                
                title = os.path.basename(filepath)
                
                doc = Document(
                    doc_id=doc_id,
                    path=filepath,
                    title=title,
                    content=content,
                    word_count=len(content.split()),
                    indexed_at=time.time()
                )
                
                self.index.add_document(doc)
                doc_id += 1
                
                if (i + 1) % 10 == 0:
                    print(f"Indexed {i + 1}/{len(files_found)} files...")
                    
            except Exception as e:
                print(f"Error indexing {filepath}: {e}")
        
        self._save_index()
        indexed = doc_id - self.index.doc_count + self.index.doc_count - self.index.doc_count
        print(f"Indexed {self.index.doc_count} documents total")
        return self.index.doc_count
    
    def crawl_web(self, url: str) -> int:
        """Crawl web pages starting from a URL."""
        print(f"Starting web crawl from: {url}")
        
        def progress(current, url):
            print(f"Crawled {current}: {url[:50]}...")
        
        crawler = WebCrawler()
        count = crawler.crawl(url, self.index, progress)
        
        self._save_index()
        print(f"Crawled {count} pages")
        return count
    
    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search indexed documents."""
        return self.ranker.rank_documents(query, limit)
    
    def get_stats(self) -> Dict:
        """Get index statistics."""
        return {
            'total_documents': self.index.get_total_documents(),
            'total_terms': len(self.index.term_doc_freq),
            'index_path': self.index_path
        }
    
    def clear_index(self):
        """Clear the entire index."""
        self.index.clear()
        if os.path.exists(self.index_path):
            os.remove(self.index_path)
        print("Index cleared")


# ============== CLI Interface ==============
class CLI:
    """Command-line interface for the search engine."""
    
    def __init__(self):
        self.engine = SearchEngine()
        self.commands = {
            'help': self.cmd_help,
            'index': self.cmd_index,
            'search': self.cmd_search,
            'crawl': self.cmd_crawl,
            'stats': self.cmd_stats,
            'clear': self.cmd_clear,
            'exit': self.cmd_exit,
            'quit': self.cmd_exit,
        }
    
    def run(self):
        """Run the CLI."""
        print("\n" + "=" * 60)
        print("  SimpleSearch - Document Search Engine")
        print("=" * 60)
        print("Type 'help' for available commands\n")
        
        while True:
            try:
                user_input = input("search> ").strip()
                
                if not user_input:
                    continue
                
                parts = user_input.split(maxsplit=1)
                cmd = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                if cmd in self.commands:
                    if cmd in ['exit', 'quit']:
                        self.commands[cmd](args)
                        break
                    else:
                        self.commands[cmd](args)
                else:
                    print(f"Unknown command: {cmd}")
                    print("Type 'help' for available commands")
                    
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except EOFError:
                break
    
    def cmd_help(self, args: str):
        """Show help message."""
        print("""
Available commands:
  index <directory>  - Index all text files in a directory
  search <query>     - Search indexed documents
  crawl <url>        - Crawl web pages starting from a URL
  stats              - Show index statistics
  clear              - Clear the index
  help               - Show this help message
  exit               - Exit the program

Search tips:
  - Use quotes for exact phrase: "exact phrase"
  - Results are ranked by TF-IDF relevance
  - Longer, more specific queries yield better results
""")
    
    def cmd_index(self, args: str):
        """Index a directory."""
        if not args:
            print("Usage: index <directory>")
            return
        
        print(f"Indexing directory: {args}")
        count = self.engine.index_directory(args)
        print(f"Done! Indexed {count} documents")
    
    def cmd_search(self, args: str):
        """Search documents."""
        if not args:
            print("Usage: search <query>")
            return
        
        results = self.engine.search(args)
        
        if not results:
            print("No results found")
            return
        
        print(f"\nFound {len(results)} results:\n")
        print("-" * 60)
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.title}")
            print(f"   Path: {result.path}")
            print(f"   Score: {result.score:.4f}")
            print(f"   Snippet: {result.snippet[:100]}...")
            print("-" * 60)
    
    def cmd_crawl(self, args: str):
        """Crawl web pages."""
        if not args:
            print("Usage: crawl <url>")
            return
        
        if not args.startswith(('http://', 'https://')):
            args = 'https://' + args
        
        count = self.engine.crawl_web(args)
        print(f"Crawled {count} pages")
    
    def cmd_stats(self, args: str):
        """Show index statistics."""
        stats = self.engine.get_stats()
        print(f"""
Index Statistics:
  Total Documents: {stats['total_documents']}
  Total Terms: {stats['total_terms']}
  Index File: {stats['index_path']}
""")
    
    def cmd_clear(self, args: str):
        """Clear the index."""
        confirm = input("Are you sure you want to clear the index? (y/n): ")
        if confirm.lower() == 'y':
            self.engine.clear_index()
    
    def cmd_exit(self, args: str):
        """Exit the program."""
        print("Goodbye!")


# ============== Main Entry Point ==============
def main():
    """Main entry point."""
    import sys
    
    if len(sys.argv) > 1:
        # Command-line mode
        engine = SearchEngine()
        cmd = sys.argv[1].lower()
        
        if cmd == 'index' and len(sys.argv) > 2:
            engine.index_directory(sys.argv[2])
        elif cmd == 'search' and len(sys.argv) > 2:
            results = engine.search(sys.argv[2])
            if not results:
                print("No results found")
            for r in results:
                print(f"{r.title}: {r.score:.4f}")
        elif cmd == 'crawl' and len(sys.argv) > 2:
            engine.crawl_web(sys.argv[2])
        elif cmd == 'stats':
            stats = engine.get_stats()
            print(f"Documents: {stats['total_documents']}, Terms: {stats['total_terms']}")
        elif cmd == 'clear':
            engine.clear_index()
        else:
            print("Usage: python search_engine.py [index|search|crawl|stats|clear] [args]")
    else:
        # Interactive mode
        cli = CLI()
        cli.run()


if __name__ == "__main__":
    main()