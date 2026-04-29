from preprocess import tokenize

class SearchEngine:
    def __init__(self, index, ranker, documents):
        self.index = index
        self.ranker = ranker
        self.documents = documents

    def search(self, query, method="bm25"):
        tokens = tokenize(query)

        if method == "tfidf":
            scores = self.ranker.tfidf(tokens)
        else:
            scores = self.ranker.bm25(tokens)

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        results = [
            (doc_id, score, self.documents[doc_id])
            for doc_id, score in ranked
        ]

        return results