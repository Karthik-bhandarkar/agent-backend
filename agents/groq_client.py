# backend/agents/groq_client.py
"""
Shared factory for the Groq-hosted LLM client.

Every agent (diet, fitness, symptom, lifestyle, supervisor, etc.) calls
get_llm() to obtain the same configured model instance instead of
constructing ChatGroq directly, keeping model settings in one place.
"""

from langchain_groq import ChatGroq
from config import GROQ_API_KEY, MODEL_NAME


def get_llm():
    """
    Build a ChatGroq client using the app's configured API key and model.

    Returns:
        ChatGroq: configured with low temperature (0.2) for consistent,
        less "creative" wellness advice, and a 512-token cap to keep
        responses short across all agents.
    """
    return ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model=MODEL_NAME,
        temperature=0.2,
        max_tokens=512
    )
