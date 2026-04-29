from storage import load_documents
from index import InvertedIndex
from rank import Ranker
from search import SearchEngine

def main():
    docs = load_documents("data/documents.json")

    index = InvertedIndex()
    index.build(docs)

    ranker = Ranker(index)
    engine = SearchEngine(index, ranker, docs)

    print("Simple Search Engine (type 'exit' to quit)\n")

    while True:
        query = input("Search: ")

        if query.lower() == "exit":
            break

        results = engine.search(query)

        print("\nResults:\n")
        for doc_id, score, text in results[:5]:
            print(f"[{doc_id}] Score: {score:.4f}")
            print(f"  {text}\n")

if __name__ == "__main__":
    main()