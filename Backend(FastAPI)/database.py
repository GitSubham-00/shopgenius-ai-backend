# database.py

import os
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import hashlib

load_dotenv()

# -----------------------------
# MONGO CONNECTION
# -----------------------------
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    print("[database] ❌ MONGO_URI missing in .env!")

print("[database] MONGO_URI Loaded:", bool(MONGO_URI))

client = MongoClient(MONGO_URI) if MONGO_URI else None
db = client["shopping_assistant_"] if client is not None else None

# Collections (⚠ FIXED boolean usage)
search_col = db["search_history_"] if db is not None else None
price_col = db["price_history_"] if db is not None else None
users_col = db["users"] if db is not None else None


# -----------------------------
# PASSWORD HASHING
# -----------------------------
def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()


# -----------------------------
# AUTO-CREATE DEFAULT ADMIN
# -----------------------------
def ensure_admin_exists():
    if users_col is not None:
        admin_exists = users_col.find_one({"role": "admin"})
        if admin_exists:
            print("[database] ✔ Admin already exists")
            return

        users_col.insert_one({
            "name": "Subham",
            "email": "work.subham2004@gmail.com",
            "password": hash_password("admin123"),
            "role": "admin",
            "created_at": datetime.utcnow()
        })

        print("[database] ⭐ Default Admin Created:")
        print("    Email: work.subham2004@gmail.com")
        print("    Password: admin123")
    else:
        print("[database] ❌ Users collection missing")


# Run on import
ensure_admin_exists()


# -----------------------------
# USER FUNCTIONS
# -----------------------------
def create_user(name, email, password, role="user"):
    if users_col is None:
        return False, "Database not available."

    if users_col.find_one({"email": email}):
        return False, "Email already exists."

    users_col.insert_one({
        "name": name,
        "email": email,
        "password": hash_password(password),
        "role": role,
        "created_at": datetime.utcnow()
    })

    return True, "Account created successfully."


def validate_login(email, password):
    if users_col is None:
        return None

    return users_col.find_one({
        "email": email,
        "password": hash_password(password)
    })


def get_all_users():
    if users_col is None:
        return []
    return list(users_col.find())


def delete_user(email):
    if users_col is not None:
        users_col.delete_one({"email": email})


def update_user_role(email, new_role):
    if users_col is not None:
        users_col.update_one({"email": email}, {"$set": {"role": new_role}})


# -----------------------------
# SEARCH & PRICE HISTORY
# -----------------------------
def save_data(query, products):
    if search_col is not None:
        search_col.insert_one({
            "query": query,
            "total": len(products),
            "products": products,
            "timestamp": datetime.utcnow()
        })


def save_price_history(products):
    if price_col is not None:
        for p in products:
            price_col.insert_one({
                "title": p.get("title"),
                "price": p.get("price"),
                "timestamp": datetime.utcnow()
            })


def get_price_history(title):
    if price_col is None:
        return []
    return list(price_col.find({"title": title}).sort("timestamp", -1))
