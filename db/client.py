# backend/db/client.py
"""
MongoDB connection and client setup.
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
if not MONGO_URI:
    raise RuntimeError("MONGODB_URI missing in .env")

# Try to connect but don't let failures crash the process.
client = None
db = None
users_collection = None
profiles_collection = None
conversation_collection = None

# Determine DB name from URI (the path part before query params), fallback to FitAura
try:
    db_name = MONGO_URI.split("/")[-1].split("?")[0] or "FitAura"
except Exception:
    db_name = "FitAura"

try:
    # Use a short timeout so server starts quickly if DNS/network fails
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Small ping to validate connection
    client.admin.command("ping")
    db = client[db_name]
    users_collection = db["users"]
    profiles_collection = db["profiles"]
    conversation_collection = db["conversation_turns"]
    print("MongoDB connected.")
except Exception as e:
    # Keep server alive — log helpful message
    print("WARNING: MongoDB connection failed at startup:", repr(e))
    client = None
    db = None
    users_collection = None
    profiles_collection = None
    conversation_collection = None


# Helper to ensure collection availability
def _ensure_collection(coll, name: str = "collection"):
    if coll is None:
        raise RuntimeError(
            f"Database not connected. '{name}' is unavailable. "
            "Check MONGODB_URI, network access, DNS, or install dnspython for mongodb+srv."
        )
    return coll
