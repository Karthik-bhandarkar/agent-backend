# backend/agents/fitness_agent.py
"""
Agent responsible for generating exercise and fitness recommendations.

Reads the current orchestration state and the user's health profile to provide
tailored workout plans and posture advice, accounting for safety constraints
identified by prior agents. Its output is captured by the orchestrator and
written into the shared state dictionary under the `FitnessAgent` key.
"""
from agents.groq_client import get_llm
llm = get_llm()

def run_fitness_agent(state, profile):
    """
    Invoke the Fitness Agent LLM chain.

    Args:
        state: The current orchestration state containing outputs from any
            agents that have already run during this turn.
        profile: The user's health profile (metrics, goals, conditions).

    Returns:
        str: A concise markdown section analyzing how other agents' findings
        affect fitness, followed by a specific workout plan.
    """
    prompt = f"""
You are the FitnessAgent in a Digital Wellness multi-agent system.

Your job:
- Provide PRACTICAL and ACTIONABLE fitness guidance.
- Use user profile + extracted state from previous agents.
- Do NOT repeat what the user already said.
- Focus on exercises, routine improvements, posture, stamina, energy, motivation.

User Profile:
{profile}

State (information extracted by previous agents):
{state}

RESPONSE RULES:
- Review outputs from Symptom, Diet, and Lifestyle agents.
- "Symptom agent noted X, Diet suggested Y..." -> "Therefore I recommend Z."
- Safety Check: If symptoms (e.g. back pain) contraindicate certain exercises, explicitely say "Avoid X due to back pain".
- Format:
  - **Analysis**: How other agents' findings affect fitness.
  - **Workout Plan**: Specific exercises adjusted for safety.
- Keep it concise, action-oriented.

Now provide a concise, helpful fitness response.
"""
    return llm.invoke(prompt).content.strip()
