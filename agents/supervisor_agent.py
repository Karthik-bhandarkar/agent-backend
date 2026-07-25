# backend/agents/supervisor_agent.py
"""
Agent responsible for routing decisions in the multi-agent orchestration.

Reads the user's message, their profile, the conversation history, and the
current state (which agents have already run) to decide the next step. It
does not write to the state dictionary itself; it returns the name of the next
agent to run, or "FINISH" to terminate the loop.
"""

import json
import re
from typing import Optional
from langchain_core.prompts import PromptTemplate
from core.logging_config import get_logger
from agents.groq_client import get_llm

llm = get_llm()
logger = get_logger(__name__)

def extract_json_block(text: str) -> Optional[dict]:
    """Extract the first JSON object from a string, handling markdown fences."""
    # Try to find a JSON block between backticks
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        # Fallback: find the first { ... } block
        match = re.search(r'(\{.*?\})', text, re.DOTALL)
        if not match:
            return None
        json_str = match.group(1)
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None

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

OUTPUT FORMAT (STRICT):
Respond with ONLY the JSON object. No reasoning, no explanation, no markdown fences, no text before or after. Your entire response must be parseable by json.loads() as-is.
Example: {{"next_agent": "SymptomAgent"}} or {{"next_agent": "FINISH"}}
""",
    input_variables=["conversation_history", "user_message", "profile", "cleaned_state", "intent"]
)

# Create the Chain
supervisor_chain = supervisor_prompt | llm

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
        
        # The result from llm without parser is an AIMessage
        raw_text = result.content
        parsed_json = extract_json_block(raw_text)
        
        if parsed_json and "next_agent" in parsed_json:
            return parsed_json["next_agent"]
        else:
            logger.error(f"Failed to extract valid JSON from Supervisor LLM output. Raw text:\n{raw_text}")
            return "FINISH"

    except Exception as e:
        logger.error(f"Supervisor Error: {e}")
        return "FINISH"
