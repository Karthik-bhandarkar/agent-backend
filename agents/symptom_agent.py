# backend/agents/symptom_agent.py

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
    Executes the Symptom Agent Chain.
    """
    try:
        response = symptom_chain.invoke({
            "message": message,
            "profile": str(profile) if profile else "None"
        })
        return response.strip()
    except Exception as e:
        return f"Error analyzing symptoms: {str(e)}"