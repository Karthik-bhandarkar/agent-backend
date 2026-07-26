# backend/config.py
"""
Configuration and environment variables.

Centralizes all environment variables (API keys, JWT settings, model name)
by loading them from .env. Other modules import these constants instead of
calling os.getenv() directly.
"""
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Support both JWT_SECRET and JWT_SECRET_KEY (Render may have either)
JWT_SECRET = os.getenv("JWT_SECRET") or os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET (or JWT_SECRET_KEY) is missing from environment variables!")
JWT_ALGORITHM = "HS256"

# Define the specific LLM model used by all agents in the pipeline
MODEL_NAME = "llama-3.1-8b-instant"
