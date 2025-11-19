# nlp_engine.py

import re
import spacy

nlp = spacy.load("en_core_web_sm")

CATEGORIES = {
    "phone": ["phone", "mobile", "smartphone", "iphone"],
    "laptop": ["laptop", "notebook", "macbook"],
    "shoes": ["shoe", "sneaker"],
    "saree": ["saree", "sari"]
}

def extract_price(text: str):
    pattern = r"(under|below|less than|<)\s?([\d,]+)"
    match = re.search(pattern, text.lower())
    if match:
        return int(match.group(2).replace(",", ""))
    return None

def extract_category(text: str):
    t = text.lower()
    for cat, keys in CATEGORIES.items():
        if any(k in t for k in keys):
            return cat
    return None

def extract_keywords(q: str):
    doc = nlp(q)
    return " ".join([t.text for t in doc if t.pos_ in ["NOUN", "ADJ", "NUM", "PROPN"]])

def parse_query(user_query: str):
    print(f"[nlp_engine] Parsing: {user_query}")
    return {
        "keywords": extract_keywords(user_query),
        "price_limit": extract_price(user_query),
        "category": extract_category(user_query),
        "brand": None  # safe fallback
    }

# --------------------------------------------------------
# IMPROVED COMPARISON EXTRACTION
# --------------------------------------------------------
def extract_compare_products(text: str):
    text = text.lower().strip()

    # Supported patterns:
    patterns = [
        r"compare (.+?) vs (.+)",
        r"compare (.+?) and (.+)",
        r"compare (.+?) with (.+)",
        r"compare between (.+?) and (.+)"
    ]

    for p in patterns:
        match = re.search(p, text)
        if match:
            p1 = match.group(1).strip()
            p2 = match.group(2).strip()
            print(f"[nlp_engine] Compare detected: {p1} VS {p2}")
            return p1, p2

    return None, None
