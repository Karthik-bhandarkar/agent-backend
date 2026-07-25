# backend/agents/diet_agent.py
"""
Agent responsible for generating dietary and nutritional recommendations.

Reads the current orchestration state (including the outputs of any previously
run agents) and the user's health profile to generate personalized food advice.
Its output is captured by the orchestrator and written into the shared state
dictionary under the `DietAgent` key for downstream agents to reference.
"""
from agents.groq_client import get_llm
from typing import Optional

llm = get_llm()

def run_diet_agent(state: dict, profile: Optional[dict]) -> str:
    """
    Invoke the Diet Agent LLM chain.

    Args:
        state: The current orchestration state containing outputs from any
            agents that have already run during this turn.
        profile: The user's health profile (metrics, goals, conditions).

    Returns:
        str: A short, practical markdown section containing a critique of
        prior findings and a specific nutritional plan.
    """

    prompt = f"""
You are the DietAgent in a wellness assistant.

You must:
- Give simple, practical diet suggestions.
- Use the user's profile if available (age, weight, height, diet_type, goal, health_conditions).
- NEVER ask the user questions.
- NEVER say "I need more info".
- Keep the answer short (4–6 lines max).
- Adapt food suggestions to their diet_type (veg, non-veg, eggetarian, vegan).

User profile (may be null):
{profile}

Previous agent notes (state):
{state}

Your output:
- Analyzes the Symptom Agent's findings (if any).
- "I see the user has [symptoms]..."
- Suggest nutritional interventions that specifically help those symptoms.
- Critique/Refine: If a previous agent missed a nutritional angle, add it.
- Format:
  - **Critique**: "Symptom agent identified X, so I recommend Y."
  - **Plan**: Specific foods to eat/avoid.
"""

    response = llm.invoke(prompt).content
    return response.strip()
