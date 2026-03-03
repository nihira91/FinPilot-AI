# tests/test_llm.py
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash"
)
response = llm.invoke("Hello, are you working?")
print(response.content)