from collections import defaultdict
from preprocess import tokenize

class InvertedIndex:
    def __init__(self):
        self.index = defaultdict(dict)   # term -> {doc_id: tf}
        self.doc_lengths = {}            # doc_id -> length
        self.total_docs = 0

    def build(self, documents):
        self.total_docs = len(documents)

        for doc_id, text in documents.items():
            tokens = tokenize(text)
            self.doc_lengths[doc_id] = len(tokens)

            for token in tokens:
                self.index[token][doc_id] = (
                    self.index[token].get(doc_id, 0) + 1
                )