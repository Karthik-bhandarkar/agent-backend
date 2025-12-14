from agents.groq_client import get_llm

llm = get_llm()

def synthesize_output(state: dict, message: str) -> str:
    """
    Generate a SHORT, SIMPLE, USER-FRIENDLY summary that answers the User's Message.
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
