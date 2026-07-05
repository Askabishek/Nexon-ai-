import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv(override=True)

# -------------------------
# CONNECTION
# -------------------------

MONGO_URI = os.getenv("MONGO_URI")
print("URI LOADED:", repr(MONGO_URI))  # Debugging line to check if MONGO_URI is loaded correctly

client = MongoClient(MONGO_URI)

try:
    client.admin.command("ping")
    print("✅ MongoDB Connected")
except Exception as e:
    print("❌ Connection Failed:", e)



if not MONGO_URI:
    raise ValueError("MONGO_URI is not set in environment variables")

client = MongoClient(MONGO_URI)

# Database
db = client["nexora_ai"]

# Collections
users_col = db["users"]
chat_col = db["chat_history"]
pref_col = db["preferences"]

# -------------------------
# USER FUNCTIONS
# -------------------------

def create_or_update_user(user):
    try:
        users_col.update_one(
            {"firebase_uid": user["firebase_uid"]},
            {"$set": user},
            upsert=True
        )
    except Exception as e:
        print("MongoDB User Error:", e)


def get_user(user_id):
    try:
        return users_col.find_one({"firebase_uid": user_id})
    except Exception as e:
        print("MongoDB Get User Error:", e)
        return None

# -------------------------
# CHAT HISTORY (MAIN)
# -------------------------

def log_interaction(user_id, query, response):
    try:
        print("Inside log_interaction")

        result = chat_col.insert_one({
            "user_id": user_id,
            "query": query,
            "response": response,
            "timestamp": datetime.utcnow()
        })

        print("Inserted:", result.inserted_id)

    except Exception as e:
        print("MongoDB Log Error:", e)

# -------------------------
# PREFERENCES
# -------------------------

def save_preferences(user_id, preferences):
    try:
        pref_col.update_one(
            {"user_id": user_id},
            {"$set": preferences},
            upsert=True
        )
    except Exception as e:
        print("MongoDB Preference Save Error:", e)


def get_preferences(user_id):
    try:
        return pref_col.find_one({"user_id": user_id})
    except Exception as e:
        print("MongoDB Preference Fetch Error:", e)
        return None