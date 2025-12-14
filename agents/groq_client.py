from langchain_groq import ChatGroq
from config import GROQ_API_KEY, MODEL_NAME

def get_llm():
    return ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model=MODEL_NAME,
        temperature=0.2,
        max_tokens=512
    )
