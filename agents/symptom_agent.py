# backend/agents/symptom_agent.py
"""
Agent responsible for analyzing physical and mental health symptoms.

Reads the user's message and health profile to generate a concise summary
of potential causes and risk levels. Its output is captured by the
orchestrator and written into the shared state dictionary under the
`SymptomAgent` key for downstream agents to reference.
"""

from typing import Optional
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from agents.groq_client import get_llm

llm = get_llm()

# Define Prompt Template
symptom_prompt = PromptTemplate(
    template="""You are the SymptomAgent in a wellness assistant.

Your job:
- Analyze the user's symptoms.
- Provide a STRICTLY concise keyword summary.

User message:
{message}

User profile:
{profile}

RESPONSE RULES:
- **Conciseness is Key**. No paragraphs.
- Format output as a BULLETED LIST:
  - **Symptoms**: [Comma-separated keywords]
  - **Duration**: [e.g., 5 days] (if mentioned)
  - **Potential Causes**: [Max 1 sentence analysis]
  - **Risk Level**: [Low/Medium/High] - [Brief reason]
  - **Medical Markers**: [e.g., Vit D: 15 ng/ml] (if mentioned)

CRITICAL: If user asks to analyze a PDF but none is present, output ONLY: "Please upload your medical report PDF."
""",
    input_variables=["message", "profile"]
)

# Create Chain
symptom_chain = symptom_prompt | llm | StrOutputParser()

def run_symptom_agent(message: str, profile: Optional[dict]) -> str:
    """
    Invoke the Symptom Agent LLM chain.

    Args:
        message: The raw text of the user's input.
        profile: The user's health profile (metrics, goals, conditions).

    Returns:
        str: A bulleted list summarizing symptoms, duration, potential
        causes, and risk level.
    """
    try:
        response = symptom_chain.invoke({
            "message": message,
            "profile": str(profile) if profile else "None"
        })
        return response.strip()
    except Exception as e:
        return f"Error analyzing symptoms: {str(e)}"