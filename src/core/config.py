import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

def get_llm():
    """Initializes and returns the LLM instance."""
    return ChatOpenAI(
        model="deepseek-chat", 
        api_key=os.environ.get("DEEPSEEK_API_KEY", "sk-placeholder"),
        base_url="https://api.deepseek.com",
        temperature=0
    )
