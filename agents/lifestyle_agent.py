from agents.groq_client import get_llm
from typing import Optional

llm = get_llm()

def run_lifestyle_agent(message: str, profile: Optional[dict], state: dict = None) -> str:
    """
    Provides short, actionable lifestyle improvements.
    No long lists, no questionnaires, no generic lectures.
    """

    prompt = f"""
You are the LifestyleAgent in a wellness assistant.

Your job:
Give SHORT, ACTIONABLE lifestyle suggestions related to:
- routine
- sleep
- habits
- consistency
- stress
- time management


RESPONSE RULES:
- Use as few sentences as possible.
- Prefer 3–5 short bullet points.
- NEVER exceed 6 short sentences.
- Avoid long explanations or big paragraphs.
- Do NOT repeat the user's message.
- Do NOT ask the user for more details if profile already exists.
.

User message:
\"\"\"{message}\"\"\"

User Profile:
{profile}

State (previous agent insights):
{state}

Give ONLY helpful lifestyle tips. Refine or support previous agent suggestions if present.
"""

    response = llm.invoke(prompt).content
    return response.strip()
