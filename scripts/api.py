import json
from fastapi import FastAPI
from groq import Groq
import os

app = FastAPI()

api_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else Groq()

def get_system_prompt(account_id: str = "account_1", version: str = "v1") -> str:
    """Load the generated Retell Agent Spec to act as the system prompt."""
    file_path = f"/home/node/outputs/accounts/{account_id}/{version}/agent_spec.json"
    
    # Check if we are running locally instead of in Docker
    if not os.path.exists(file_path):
        local_path = f"outputs/accounts/{account_id}/{version}/agent_spec.json"
        if os.path.exists(local_path):
            file_path = local_path
            
    try:
        with open(file_path, "r") as f:
            spec = json.load(f)
            return spec.get("system_prompt", "You are a helpful AI voice assistant.")
    except Exception as e:
        print(f"Error loading prompt: {e}")
        return "You are a helpful AI voice assistant."

@app.get("/")
async def root():
    return {"message": "Clara AI Retell API is running. Point Retell to /retell"}

@app.post("/retell")
async def retell_llm(payload: dict):
    user_text = payload.get("transcript", "")
    
    # Here you could dynamically grab account_id if Retell passes it in custom variables
    # For now, we default to the account_1 v1 demo
    system_prompt = get_system_prompt()

    completion = client.chat.completions.create(
        model=os.environ.get("LLM_MODEL", "llama3-70b-8192"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ],
        temperature=0.2,
    )

    response = completion.choices[0].message.content

    return {
        "response": response
    }
