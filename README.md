# 🔎 Simple Search Engine

A lightweight search engine built in Python that can **crawl, index, and rank documents** using classic information retrieval techniques like **Inverted Indexing** and **TF-IDF / BM25 ranking**.

---

## 🚀 Features

* ✅ Tokenization & text preprocessing
* ✅ Inverted index for fast lookups
* ✅ TF-IDF ranking
* ✅ BM25 ranking (improved relevance)
* ✅ Keyword-based search queries
* ✅ Ranked results by relevance score
* ✅ CLI interface for searching
* ⭐ (Bonus) Basic web crawler support

---

## 📂 Project Structure

```
search_engine/
│
├── main.py              # CLI interface
├── preprocess.py        # Tokenization & cleaning
├── index.py             # Inverted index implementation
├── rank.py              # TF-IDF and BM25 ranking
├── search.py            # Query processing
├── storage.py           # Load documents
├── crawler.py           # (Optional) Web crawler
│
├── data/
│   └── documents.json   # Dataset
│
└── README.md
```

---

## ⚙️ How It Works

### 1. Preprocessing

* Converts text to lowercase
* Tokenizes into words
* Removes common stopwords

### 2. Inverted Index

Maps each word to documents where it appears:

```
word → {doc_id: term_frequency}
```

This allows fast lookup of relevant documents.

---

### 3. Ranking Algorithms

#### 🔹 TF-IDF

* **TF (Term Frequency):** how often a term appears in a document
* **IDF (Inverse Document Frequency):** importance of the term across all documents

Formula:

```
Score = TF × IDF
```

---
Picture samples:
<img width="956" height="482" alt="Search-engine test 2" src="https://github.com/user-attachments/assets/21f771f0-c6dc-4d0f-b2cf-d77a46e437ab" />
<img width="958" height="484" alt="Search-engine test 1" src="https://github.com/user-attachments/assets/234020a9-4821-4fe6-b9dc-2c664eb307b6" />


#### 🔹 BM25 (Recommended)

Improves TF-IDF by:

* Normalizing document length
* Reducing bias toward long documents

---

### 4. Search Process

1. User enters query
2. Query is tokenized
3. Matching documents are retrieved
4. Scores are computed (TF-IDF / BM25)
5. Results are ranked and displayed

---

## ▶️ How to Run

### 1. Clone or download the project

### 2. Navigate to the folder

```
cd search_engine
```

### 3. Run the program

```
python main.py
```

### 4. Example usage

```
Search: search engine

Results:
[2] Score: 2.45
  Python is great for building a simple search engine
```

Type `exit` to quit.

---

## 📊 Example Dataset

Located in:

```
data/documents.json
```

Example:

```json
{
  "1": "This is a good movie with great acting",
  "2": "Search engines use inverted indexes",
  "3": "Python is useful for building search systems"
}
```

---

## ⚡ Performance Considerations

* Uses dictionary-based indexing for fast lookups
* Efficient term frequency counting
* Scalable to moderately large datasets
* Can be extended to disk-based storage

---

## 🌐 Bonus Features

* Basic web crawler (`crawler.py`) using requests + BeautifulSoup
* Can extract text and links from web pages

---

## 🚧 Limitations

* Exact keyword matching only (no synonyms)
* No stemming/lemmatization
* No fuzzy search
* Limited scalability for very large datasets

---

## 🔮 Future Improvements

* Phrase search (positional index)
* Stemming (e.g., Porter Stemmer)
* Fuzzy matching (edit distance)
* Web interface (Flask)
* Persistent index storage (SQLite / disk-based)
* Semantic search using embeddings

---

## 🧠 Key Concepts Used

* Information Retrieval
* Inverted Index
* TF-IDF
* BM25 Ranking
* Tokenization & Text Processing

---

## 📜 License

MIT.

---

## 👨‍💻 Author

Developed as part of a search engine implementation task.
