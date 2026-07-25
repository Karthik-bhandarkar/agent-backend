# backend/agents/intention_classifier.py
"""
Agent responsible for categorizing user intent.

Reads the raw user message and determines if it is health/wellness-related
before engaging the full agent orchestration pipeline. This agent does not
write to the shared state dictionary, as it runs as a pre-check before
the supervisor is invoked.
"""
import json
from agents.groq_client import get_llm

llm = get_llm()

def _extract_json(text: str):
    """
    Attempt to extract a valid JSON object from the LLM's raw text output.

    Args:
        text: The raw string response from the LLM.

    Returns:
        dict | None: The parsed JSON dictionary if successful, or None if
        no valid JSON block is found or decoding fails.
    """
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None

def classify_intent(message: str):
    """
    Determine if a user's message pertains to health, wellness, or medical reports.

    Args:
        message: The raw text of the user's input.

    Returns:
        dict: A dictionary containing the key `is_wellness` (bool).
    """
    prompt = f"""
You are an intention classifier for a digital wellness assistant.

Task:
- Decide if the message is related to health, wellness, stress, diet, fitness, sleep, OR medical report analysis.
- "Analyze my report", "Read my PDF", "What does my blood test say" are ALL valid wellness queries.

You MUST respond ONLY in JSON, with this exact format:
{{
  "is_wellness": true or false
}}

DO NOT add any explanation or extra text.

User message: "{message}"
"""
    res = llm.invoke(prompt)
    raw = res.content or ""
    data = _extract_json(raw)

    # If parsing fails, default to treating it as wellness (so the app continues)
    # NOTE: The LLM occasionally wraps JSON in prose, causing the parser to fail.
    # Defaulting to True ensures the user still gets a response rather than a crash.
    if not data or "is_wellness" not in data:
        data = {"is_wellness": True}

    return data
