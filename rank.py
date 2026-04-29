import math

class Ranker:
    def __init__(self, index):
        self.index = index

    def idf(self, term):
        df = len(self.index.index.get(term, {}))
        return math.log((self.index.total_docs + 1) / (df + 1)) + 1

    def tfidf(self, query_tokens):
        scores = {}

        for token in query_tokens:
            postings = self.index.index.get(token, {})
            idf = self.idf(token)

            for doc_id, tf in postings.items():
                scores[doc_id] = scores.get(doc_id, 0) + tf * idf

        return scores

    # Optional BM25 (better ranking)
    def bm25(self, query_tokens, k=1.5, b=0.75):
        scores = {}
        avg_len = sum(self.index.doc_lengths.values()) / self.index.total_docs

        for token in query_tokens:
            postings = self.index.index.get(token, {})
            df = len(postings)
            idf = math.log((self.index.total_docs - df + 0.5) / (df + 0.5) + 1)

            for doc_id, tf in postings.items():
                doc_len = self.index.doc_lengths[doc_id]

                score = idf * (
                    (tf * (k + 1)) /
                    (tf + k * (1 - b + b * (doc_len / avg_len)))
                )

                scores[doc_id] = scores.get(doc_id, 0) + score

        return scores