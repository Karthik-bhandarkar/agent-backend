import json
from agents.groq_client import get_llm

llm = get_llm()

def _extract_json(text: str):
    """
    Try to extract a JSON object from the LLM text.
    If it fails, return None.
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
    if not data or "is_wellness" not in data:
        data = {"is_wellness": True}

    return data
