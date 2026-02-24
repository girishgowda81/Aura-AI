from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Any
import uvicorn
import os
import uuid
from engine import engine
import database

app = FastAPI(title="Conversational AI Backend")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str
    content: str
    reasoning_details: Optional[Any] = None

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = "openai/gpt-oss-20b:free"
    session_id: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "Conversational AI API is running"}

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        # Context management: Get history from DB
        history = database.get_history(session_id)
        
        # Current message
        user_msg = request.messages[-1].content
        
        # Safety Check
        if not engine.moderate_content(user_msg):
            return {
                "role": "assistant",
                "content": "I'm sorry, I cannot process this request due to safety policies.",
                "session_id": session_id
            }

        # Prepare messages for LLM (including reasoning_details)
        llm_messages = []
        for m in history:
            msg = {"role": m["role"], "content": m["content"]}
            if m.get("reasoning_details"):
                msg["reasoning_details"] = m["reasoning_details"]
            llm_messages.append(msg)
        
        llm_messages.append({"role": "user", "content": user_msg})
        
        # Generate response
        assistant_msg = await engine.generate_response(llm_messages, model=request.model)
        
        response_content = assistant_msg.get("content")
        reasoning_details = assistant_msg.get("reasoning_details")
        
        # Save to history
        database.save_message(session_id, "user", user_msg)
        database.save_message(session_id, "assistant", response_content, reasoning_details)
        
        return {
            "role": "assistant",
            "content": response_content,
            "reasoning_details": reasoning_details,
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    return database.get_history(session_id, limit=50)

@app.get("/sessions")
async def get_sessions():
    return database.get_all_sessions()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
