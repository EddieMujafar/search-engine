import re

STOPWORDS = {
    "the", "is", "and", "of", "to", "in", "a", "for", "on", "with"
}

def tokenize(text):
    tokens = re.findall(r"\w+", text.lower())
    return [t for t in tokens if t not in STOPWORDS]