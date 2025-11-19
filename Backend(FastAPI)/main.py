# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from deep_translator import GoogleTranslator as Translator
from api_handler import amazon_search, clean_results
from nlp_engine import parse_query, extract_compare_products
from database import save_data, save_price_history, get_price_history

app = FastAPI(title="AI Virtual Shopping Assistant API")

# ------------------------------------------------
# CORS FOR RENDER DEPLOYMENT
# ------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # Allow Streamlit frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------
# PRICE CONVERSION USD → INR
# ------------------------------------------------
def convert_price_to_inr(price_str):
    try:
        if not price_str:
            return None
        digits = "".join([c for c in price_str if c.isdigit() or c == "."])
        if not digits:
            return price_str
        inr = float(digits) * 83
        return f"₹ {inr:,.2f}"
    except:
        return price_str


@app.get("/")
def home():
    return {"status": "OK", "message": "API Running"}


# ------------------------------------------------
# SEARCH ENDPOINT
# ------------------------------------------------
@app.get("/search")
def search(query: str):

    print(f"\n[API] Incoming Query → {query}")

    # 0️⃣ GREETING
    greetings = ["hi", "hello", "hey", "hii", "hola"]
    if query.lower().strip() in greetings:
        return {
            "mode": "greeting",
            "reply": "👋 Hello! How can I help you find products today?"
        }

    # 1️⃣ Translation
    try:
        query_en = Translator(source="auto", target="en").translate(query)
    except:
        query_en = query

    print(f"[API] Translated → {query_en}")

    # 2️⃣ Compare Mode
    p1, p2 = extract_compare_products(query_en)
    if p1 and p2:
        print(f"[API] Compare Mode: {p1} vs {p2}")

        r1 = amazon_search(p1)
        r2 = amazon_search(p2)

        c1 = clean_results(r1)
        c2 = clean_results(r2)

        return {
            "mode": "compare",
            "product_1": c1[0] if c1 else {},
            "product_2": c2[0] if c2 else {}
        }

    # 3️⃣ Normal Search
    parsed = parse_query(query_en)
    brand = parsed.get("brand")
    price_limit = parsed.get("price_limit")
    keywords = parsed.get("keywords", "")

    raw = amazon_search(keywords)
    cleaned = clean_results(raw, brand=brand, price_limit=price_limit)

    for c in cleaned:
        c["price"] = convert_price_to_inr(c["price"])

    if cleaned:
        save_data(query, cleaned)
        save_price_history(cleaned)

    return {
        "mode": "search",
        "query": query,
        "translated": query_en,
        "filters": parsed,
        "results": cleaned[:10]
    }


@app.get("/price-history")
def price_history(title: str):
    print(f"[API] Price History → {title}")
    history = get_price_history(title)
    return {"history": history or []}
