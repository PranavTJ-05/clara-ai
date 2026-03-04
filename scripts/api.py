from fastapi import FastAPI
from groq import Groq
import os

app = FastAPI()

api_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else Groq()

@app.get("/")
async def root():
    return {"message": "Clara AI Retell API is running. Point Retell to /retell"}

@app.post("/retell")
async def retell_llm(payload: dict):
    user_text = payload.get("transcript", "")

    completion = client.chat.completions.create(
        model=os.environ.get("LLM_MODEL", "llama3-70b-8192"),
        messages=[
            {"role": "system", "content": "You are a helpful AI voice assistant."},
            {"role": "user", "content": user_text}
        ],
        temperature=0.2,
    )

    response = completion.choices[0].message.content

    return {
        "response": response
    }
