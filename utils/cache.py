import hashlib
import time
import streamlit as st


# In-memory cache storage
if "cache" not in st.session_state:
    st.session_state.cache = {}

CACHE = st.session_state.cache

#cache expiry time in seconds (10 minutes)
CACHE_EXPIRY = 600


def generate_cache_key(query: str, context: str = "") -> str:
    """
    Generate a unique cache key using the user query
    and uploaded file context.
    """
    combined_text = (query.strip().lower() + context.strip()).encode("utf-8")
    return hashlib.md5(combined_text).hexdigest()

def get_cached_response(query: str, context: str = ""):
    key = generate_cache_key(query, context)
    print(f"🔍 Looking for cache: {key}")

    if key not in CACHE:
        print("❌ Cache MISS")
        return None

    cached_data = CACHE[key]

    # Check expiry
    if time.time() - cached_data["timestamp"] > CACHE_EXPIRY:
        del CACHE[key]
        print("⌛ Cache Expired")
        return None

    print("⚡ Cache HIT")
    print("Available Cache Keys:", list(CACHE.keys()))

    return cached_data["response"]

def save_response(query: str, context: str, response):
    """
    Save a response to cache.
    """
    key = generate_cache_key(query, context)

    CACHE[key] = {
        "response": response,
        "timestamp": time.time()
    }

    print("Current Cache Keys:", list(CACHE.keys()))



def clear_cache():
    """
    Clear the entire cache.
    """
    CACHE.clear()


def cache_size():
    """
    Return the number of cached responses.
    """
    return len(CACHE)
