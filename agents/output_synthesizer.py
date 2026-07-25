# backend/agents/output_synthesizer.py
"""
Agent responsible for merging all specialist outputs into a final report.

Reads the user's original message and the complete orchestration state
(containing outputs from all agents that ran this turn) to generate a
clean, structured Markdown response. Its output is returned by the
orchestrator and typically written to the `final_response` key.
"""
from agents.groq_client import get_llm

llm = get_llm()

def synthesize_output(state: dict, message: str) -> str:
    """
    Invoke the Synthesizer Agent LLM chain.

    Args:
        state: The complete orchestration state containing all specialist
            agent outputs from this turn.
        message: The raw text of the user's input.

    Returns:
        str: A professional Markdown-formatted health report combining all
        agent insights and answering the user's question directly.
    """

    prompt = f"""
You are the Synthesizer Agent.
Your job is to combine these agent outputs into a CLEAN, STRUCTURED Health Report that DIRECTLY ANSWERS the user's current question.

User Question: "{message}"

Agent Outputs:
{state}

REQUIRED OUTPUT FORMAT (Markdown):

### Wellness Summary
[Direct answer to the user's question first. Then briefly summarize condition.]

### 🍽 Diet Plan
- [Breakfast/Lunch/Dinner/Snack ideas based on Diet Agent]
- Hydration: [Value]
- Avoid: [List]

### 🧘 Lifestyle & Sleep Tips
- [Tip 1]
- [Tip 2]
- [Tip 3]

### 🏃 Exercise Plan
- Warm-up: [List]
- Main: [List]
- Cooldown: [List]
- Avoid: [List]

### ⚠ Disclaimer
This is general wellness guidance and not a medical diagnosis.

(Skip sections if NO data exists for them in agent outputs).
Smooth out the text to look professional.
"""
    
    response = llm.invoke(prompt).content
    return response.strip()
