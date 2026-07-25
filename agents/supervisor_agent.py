# backend/agents/supervisor_agent.py
"""
Agent responsible for routing decisions in the multi-agent orchestration.

Reads the user's message, their profile, the conversation history, and the
current state (which agents have already run) to decide the next step. It
does not write to the state dictionary itself; it returns the name of the next
agent to run, or "FINISH" to terminate the loop.
"""

import json
from typing import Optional
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from agents.groq_client import get_llm

llm = get_llm()

# Define the Output Parser
parser = JsonOutputParser()

# Define the Prompt Template
supervisor_prompt = PromptTemplate(
    template="""You are the SUPERVISOR of a multi-agent Digital Wellness Assistant.

Your role:
- Decide which ONE specialized agent should run NEXT.
- Use deep reasoning, not simple keyword matching.
- You must consider intent, profile, history, and current state.

CONVERSATION HISTORY:
{conversation_history}

CURRENT USER MESSAGE:
{user_message}

USER PROFILE:
{profile}

CURRENT ORCHESTRATION STATE (agent outputs so far in THIS turn):
{cleaned_state}

USER INTENT:
{intent}

AVAILABLE AGENTS:
1. SymptomAgent: Physical/mental symptoms, pain, fatigue, feeling unwell.
2. DietAgent: Food, nutrition, digestion, weight, diet plans.
3. FitnessAgent: Exercise, workouts, stamina, muscle, posture.
4. LifestyleAgent: Sleep, stress, habits, routines, burnout.

SELECTION GUIDELINES (VERY IMPORTANT):
1. **COMPLEX SYMPTOMS**: If user has health issues/pain, Form a TEAM: `SymptomAgent` -> `DietAgent` -> `LifestyleAgent` -> `FitnessAgent`.
2. **SPECIFIC REQUESTS**: If user asks for ONE thing (e.g. "Diet plan"), ONLY call that agent -> `FINISH`.
3. **GENERAL**: Do NOT call the same agent twice. If main need is met, `FINISH`.

OUTPUT FORMAT:
Return a JSON object with a single key "next_agent".
Example: {{"next_agent": "SymptomAgent"}} or {{"next_agent": "FINISH"}}

{format_instructions}
""",
    input_variables=["conversation_history", "user_message", "profile", "cleaned_state", "intent"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

# Create the Chain
supervisor_chain = supervisor_prompt | llm | parser

def supervisor(user_message: str, profile: Optional[dict], state: dict) -> str:
    """
    Invoke the supervisor LLM chain to determine the next agent.

    Args:
        user_message: The raw text of the user's input.
        profile: The user's health profile (metrics, goals, conditions).
        state: The current orchestration state containing outputs from any
            agents that have already run during this turn.

    Returns:
        str: The exact name of the next agent to invoke (e.g., "DietAgent"),
        or "FINISH" if the response is complete.
    """
    conversation_history = state.get("conversation_history", "No previous conversation yet.")
    intent = state.get("intent", {})
    cleaned_state = {k: v for k, v in state.items() if k not in ["conversation_history", "intent"]}

    try:
        result = supervisor_chain.invoke({
            "conversation_history": conversation_history,
            "user_message": user_message,
            "profile": str(profile),
            "cleaned_state": str(cleaned_state),
            "intent": str(intent)
        })
        
        # Robust extraction
        if isinstance(result, dict) and "next_agent" in result:
            return result["next_agent"]
        elif isinstance(result, str):
             # Fallback if parser fails but returns string key
             if "FINISH" in result: return "FINISH"
             for agent in ["SymptomAgent", "DietAgent", "FitnessAgent", "LifestyleAgent"]:
                 if agent in result: return agent
        
        return "FINISH"

    except Exception as e:
        # NOTE: JSON parsing failures often end up here when the LLM wraps
        # its JSON output in verbose text. We default to FINISH to avoid crashing.
        print(f"DEBUG: Supervisor Error: {e}")
        return "FINISH"
