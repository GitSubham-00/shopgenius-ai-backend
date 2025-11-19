# api_handler.py

import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------
# Load API Keys
# ---------------------------------------
RAPID_COPILOT_KEY = os.getenv("RAPID_COPILOT_KEY")
RAPID_COPILOT_HOST = os.getenv("RAPID_COPILOT_HOST")

RAPID_AMAZON_KEY = os.getenv("RAPID_AMAZON_KEY")
RAPID_AMAZON_HOST = os.getenv("RAPID_AMAZON_HOST")


# ---------------------------------------
# Extract brand, keywords, price
# ---------------------------------------
def parse_query(user_query: str):
    q = user_query.lower()

    brands = [
        "samsung", "vivo", "oppo", "mi", "xiaomi", "redmi",
        "realme", "apple", "iphone", "motorola", "oneplus"
    ]
    brand = next((b for b in brands if b in q), None)

    # Price (under 20000, below 15k etc.)
    price_limit = None
    patterns = [
        r"under\s*(\d+)",
        r"below\s*(\d+)",
        r"less than\s*(\d+)",
        r"under\s*(\d+)\s*k",
        r"below\s*(\d+)\s*k",
    ]
    for pat in patterns:
        match = re.search(pat, q)
        if match:
            num = int(match.group(1))
            if "k" in pat:
                num *= 1000
            price_limit = num
            break

    # Keywords
    keywords = " ".join(
        w for w in q.split() if w not in ["under", "below", "less", "than", "k"]
    )

    return {
        "brand": brand,
        "price_limit": price_limit,
        "keywords": keywords
    }


# ---------------------------------------
# Copilot Chat API
# ---------------------------------------
def copilot_chat(message: str):
    url = f"https://{RAPID_COPILOT_HOST}/copilot"
    payload = {"message": message, "mode": "CHAT", "markdown": False}
    headers = {
        "x-rapidapi-key": RAPID_COPILOT_KEY,
        "x-rapidapi-host": RAPID_COPILOT_HOST,
        "Content-Type": "application/json"
    }
    try:
        r = requests.post(url, json=payload, headers=headers)
        return r.json() if r.status_code == 200 else None
    except:
        return None


# ---------------------------------------
# Amazon Search API
# ---------------------------------------
def amazon_search(query: str, page="1"):
    print(f"[api] Searching Amazon for: {query}")

    url = f"https://{RAPID_AMAZON_HOST}/search"
    headers = {
        "x-rapidapi-key": RAPID_AMAZON_KEY,
        "x-rapidapi-host": RAPID_AMAZON_HOST
    }
    params = {"query": query, "page": page}

    try:
        r = requests.get(url, headers=headers, params=params)
        print("[api] Amazon Status:", r.status_code)
        return r.json() if r.status_code == 200 else None
    except Exception as e:
        print("[api] ERROR:", e)
        return None


# ---------------------------------------
# Clean API Results → Required Format
# ---------------------------------------
def clean_results(raw, brand=None, price_limit=None):
    if not raw or "data" not in raw:
        return []

    products = raw.get("data", {}).get("products", [])
    clean = []

    for p in products:
        title = p.get("product_title", "")
        price = p.get("product_price")
        url = p.get("product_url")
        image = p.get("product_photo")

        if not title or not url:
            continue

        # Brand filter
        if brand and brand.lower() not in title.lower():
            continue

        # Handle price safely
        try:
            num_price = float("".join(ch for ch in price if ch.isdigit() or ch == "."))
        except:
            num_price = None

        # Price limit filter
        if price_limit and num_price and num_price > price_limit:
            continue

        clean.append({
            "title": title,
            "price": price,
            "url": url,
            "image": image
        })

    # Sort ascending by price
    try:
        clean.sort(key=lambda x: float("".join(c for c in x["price"] if c.isdigit() or c == ".")))
    except:
        pass

    return clean
