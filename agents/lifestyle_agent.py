# backend/agents/lifestyle_agent.py
"""
Agent responsible for generating lifestyle, sleep, and stress management advice.

Reads the user's message, health profile, and current orchestration state to
provide concise, actionable habit improvements. Its output is captured by the
orchestrator and written into the shared state dictionary under the
`LifestyleAgent` key for downstream agents to reference.
"""
from agents.groq_client import get_llm
from typing import Optional

llm = get_llm()

def run_lifestyle_agent(message: str, profile: Optional[dict], state: dict = None) -> str:
    """
    Invoke the Lifestyle Agent LLM chain.

    Args:
        message: The raw text of the user's input.
        profile: The user's health profile (metrics, goals, conditions).
        state: The current orchestration state containing outputs from any
            agents that have already run during this turn.

    Returns:
        str: Short, actionable bullet points containing lifestyle tips that
        refine or support previous agent suggestions.
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
