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

from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/retell/{call_id}")
async def retell_websocket(websocket: WebSocket, call_id: str):
    await websocket.accept()
    print(f"Call {call_id} connected")
    
    # Initialize conversation state
    system_prompt = get_system_prompt()
    conversation_history = [
        {"role": "system", "content": system_prompt}
    ]
    
    try:
        while True:
            # Receive message from Retell
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Retell sends interaction types, we only care about user speaking ("transcript") or "update"
            if message.get("interaction_type") == "update_only":
                continue
                
            # Handle user utterance
            if message.get("interaction_type") == "response_required" or "transcript" in message:
                user_text = message.get("transcript", "")
                
                # Skip empty transcripts
                if not user_text or len(user_text) == 0:
                    continue
                    
                conversation_history.append({"role": "user", "content": user_text})
                
                try:
                    # Get response from Groq
                    completion = client.chat.completions.create(
                        model=os.environ.get("LLM_MODEL", "llama3-70b-8192"),
                        messages=conversation_history,
                        temperature=0.2,
                    )
                    
                    response_text = completion.choices[0].message.content
                    conversation_history.append({"role": "assistant", "content": response_text})
                    
                    # Send response back to Retell
                    await websocket.send_text(json.dumps({
                        "response_id": message.get("response_id", 0),
                        "content": response_text,
                        "content_complete": True,
                        "end_call": False
                    }))
                    
                except Exception as e:
                    print(f"LLM Error: {str(e)}")
                    await websocket.send_text(json.dumps({
                        "response_id": message.get("response_id", 0),
                        "content": "I'm sorry, my system is currently experiencing an error. Please try again later.",
                        "content_complete": True,
                        "end_call": False
                    }))
                    
    except WebSocketDisconnect:
        print(f"Call {call_id} disconnected")
    except Exception as e:
        print(f"Error in WebSocket: {str(e)}")
