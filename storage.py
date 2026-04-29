import json

def load_documents(path):
    with open(path, "r") as f:
        return json.load(f)