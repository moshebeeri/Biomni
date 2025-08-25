"""
NIBR Biomni Canvas Backend - Phase 1.5
FastAPI backend for Canvas integration with ChatGPT
No LangGraph dependencies - pure FastAPI + OpenAI
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import datetime
import os
import json
import asyncio
from starlette.responses import StreamingResponse

# OpenAI integration
try:
    from openai import OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except ImportError:
    openai_client = None
    OPENAI_API_KEY = None

# Development mode
DEVELOPMENT_MODE = os.getenv("NODE_ENV", "development") == "development"

app = FastAPI(
    title="NIBR Biomni Canvas Backend",
    description="FastAPI backend for NIBR Biomni Canvas, integrating with ChatGPT and later Biomni agents.",
    version="1.5.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
assistants_db: Dict[str, Dict[str, Any]] = {}
threads_db: Dict[str, Dict[str, Any]] = {}
messages_db: Dict[str, List[Dict[str, Any]]] = {}

# Create default assistant
default_assistant = {
    "assistant_id": "nibr_biomni_default",
    "name": "NIBR Biomni Assistant",
    "config": {
        "configurable": {
            "systemPrompt": "You are a helpful AI assistant for biomedical research at NIBR.",
            "temperature": 0.7,
            "model": "gpt-3.5-turbo"
        }
    },
    "metadata": {
        "user_id": "system",
        "is_default": True,
        "description": "Your NIBR Biomni research assistant"
    },
    "created_at": datetime.datetime.utcnow().isoformat(),
    "updated_at": datetime.datetime.utcnow().isoformat()
}
assistants_db["nibr_biomni_default"] = default_assistant

# Pydantic models
class Assistant(BaseModel):
    assistant_id: str
    name: str
    config: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class Thread(BaseModel):
    thread_id: str
    metadata: Dict[str, Any] = {}
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class StoreItem(BaseModel):
    table: str
    data: Dict[str, Any] = {}
    filters: Dict[str, Any] = {}

# Health check
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "version": "1.5.0",
        "mode": "development" if DEVELOPMENT_MODE else "production"
    }

# === ASSISTANT ENDPOINTS ===

@app.get("/assistants")
async def get_assistants(metadata: str = None, limit: int = 100):
    """Get all assistants"""
    assistants = list(assistants_db.values())
    
    if metadata:
        try:
            metadata_filter = json.loads(metadata)
            if "user_id" in metadata_filter:
                assistants = [a for a in assistants if 
                            a["metadata"].get("user_id") == metadata_filter["user_id"] or
                            a["metadata"].get("user_id") == "system"]
        except json.JSONDecodeError:
            pass
    
    assistants.sort(key=lambda x: x["created_at"], reverse=True)
    return assistants[:limit]

@app.get("/assistants/{assistant_id}")
async def get_assistant(assistant_id: str):
    """Get specific assistant"""
    if assistant_id not in assistants_db:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return assistants_db[assistant_id]

@app.post("/assistants")
async def create_assistant(assistant: Assistant):
    """Create new assistant"""
    assistant_id = assistant.assistant_id or str(uuid.uuid4())
    now = datetime.datetime.utcnow().isoformat()
    
    assistant_data = {
        "assistant_id": assistant_id,
        "name": assistant.name,
        "config": assistant.config,
        "metadata": assistant.metadata,
        "created_at": now,
        "updated_at": now
    }
    
    assistants_db[assistant_id] = assistant_data
    return assistant_data

@app.put("/assistants/{assistant_id}")
async def update_assistant(assistant_id: str, assistant: Assistant):
    """Update assistant"""
    if assistant_id not in assistants_db:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    assistant_data = assistants_db[assistant_id].copy()
    assistant_data.update({
        "name": assistant.name,
        "config": assistant.config,
        "metadata": assistant.metadata,
        "updated_at": datetime.datetime.utcnow().isoformat()
    })
    
    assistants_db[assistant_id] = assistant_data
    return assistant_data

@app.delete("/assistants/{assistant_id}")
async def delete_assistant(assistant_id: str):
    """Delete assistant"""
    if assistant_id in assistants_db:
        del assistants_db[assistant_id]
    return {"success": True}

# === THREAD ENDPOINTS ===

@app.get("/threads")
async def get_threads(metadata: str = None, limit: int = 100):
    """Get all threads"""
    threads = list(threads_db.values())
    
    if metadata:
        try:
            metadata_filter = json.loads(metadata)
            if "supabase_user_id" in metadata_filter:
                threads = [t for t in threads if 
                          t["metadata"].get("user_id") == metadata_filter["supabase_user_id"]]
        except json.JSONDecodeError:
            pass
    
    threads.sort(key=lambda x: x["created_at"], reverse=True)
    return threads[:limit]

@app.get("/threads/{thread_id}")
async def get_thread(thread_id: str):
    """Get specific thread"""
    if thread_id not in threads_db:
        raise HTTPException(status_code=404, detail="Thread not found")
    return threads_db[thread_id]

@app.post("/threads")
async def create_thread(request: Dict[str, Any] = None):
    """Create new thread"""
    if request is None:
        request = {}
    
    thread_id = str(uuid.uuid4())
    now = datetime.datetime.utcnow().isoformat()
    
    thread_data = {
        "thread_id": thread_id,
        "metadata": request.get("metadata", {}),
        "created_at": now,
        "updated_at": now
    }
    
    threads_db[thread_id] = thread_data
    messages_db[thread_id] = []
    
    return thread_data

@app.put("/threads/{thread_id}")
async def update_thread(thread_id: str, request: Dict[str, Any]):
    """Update thread"""
    if thread_id not in threads_db:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    thread_data = threads_db[thread_id].copy()
    thread_data.update({
        "metadata": request.get("metadata", thread_data["metadata"]),
        "updated_at": datetime.datetime.utcnow().isoformat()
    })
    
    threads_db[thread_id] = thread_data
    return thread_data

@app.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str):
    """Delete thread"""
    if thread_id in threads_db:
        del threads_db[thread_id]
    if thread_id in messages_db:
        del messages_db[thread_id]
    return {"success": True}

# === RUN ENDPOINTS ===

@app.post("/threads/{thread_id}/runs")
async def create_run(thread_id: str, run_request: Dict[str, Any]):
    """Create and stream a run"""
    if thread_id not in threads_db:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Extract assistant_id and input from request
    assistant_id = run_request.get("assistant_id", "nibr_biomni_default")
    user_input = ""
    
    # Extract user input from various possible formats
    if "input" in run_request:
        input_data = run_request["input"]
        if isinstance(input_data, dict):
            if "messages" in input_data and input_data["messages"]:
                # Get last message content
                last_msg = input_data["messages"][-1]
                if isinstance(last_msg, dict) and "content" in last_msg:
                    user_input = last_msg["content"]
            elif "content" in input_data:
                user_input = input_data["content"]
        elif isinstance(input_data, str):
            user_input = input_data
    
    if not user_input:
        user_input = "Hello! How can I help you today?"
    
    print(f"🚀 Processing: {user_input}")
    
    # Initialize messages for thread if needed
    if thread_id not in messages_db:
        messages_db[thread_id] = []
    
    # Add user message
    user_message = {
        "id": str(uuid.uuid4()),
        "type": "human",
        "content": user_input,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    messages_db[thread_id].append(user_message)

    async def generate_response():
        try:
            # Try ChatGPT if available, otherwise use mock response
            if openai_client and OPENAI_API_KEY:
                print("🤖 Using ChatGPT")
                # Call ChatGPT
                completion = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful AI assistant for biomedical research at NIBR. Be concise but informative."},
                        {"role": "user", "content": user_input}
                    ],
                    stream=True
                )
                
                full_response = ""
                for chunk in completion:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        yield content
                        await asyncio.sleep(0.01)
                
                # Add assistant message to thread
                assistant_message = {
                    "id": str(uuid.uuid4()),
                    "type": "ai",
                    "content": full_response,
                    "created_at": datetime.datetime.utcnow().isoformat(),
                }
                messages_db[thread_id].append(assistant_message)
                        
            else:
                print("🎭 Using mock response")
                # Fallback mock response
                mock_response = f"Thank you for your message: '{user_input}'. This is a mock response from the NIBR Biomni Canvas backend. In Phase 2, this will be powered by real Biomni agents with access to biomedical research data and tools."
                
                # Stream the mock response word by word
                words = mock_response.split()
                full_response = ""
                for word in words:
                    full_response += word + " "
                    yield word + " "
                    await asyncio.sleep(0.1)
                
                # Add assistant message to thread
                assistant_message = {
                    "id": str(uuid.uuid4()),
                    "type": "ai", 
                    "content": full_response.strip(),
                    "created_at": datetime.datetime.utcnow().isoformat(),
                }
                messages_db[thread_id].append(assistant_message)
                        
        except Exception as e:
            print(f"❌ Error in streaming: {e}")
            yield f"Error: {str(e)}"

    return StreamingResponse(generate_response(), media_type="text/plain")

# === STORE API ENDPOINTS (for frontend compatibility) ===

@app.post("/store/get")
async def store_get(item: StoreItem):
    """Mock store get endpoint"""
    return {"data": [], "count": 0}

@app.post("/store/insert") 
async def store_insert(item: StoreItem):
    """Mock store insert endpoint"""
    return {"data": [{"id": str(uuid.uuid4()), **item.data}]}

@app.post("/store/update")
async def store_update(item: StoreItem):
    """Mock store update endpoint"""
    return {"data": [item.data]}

@app.post("/store/delete")
async def store_delete(item: StoreItem):
    """Mock store delete endpoint"""
    return {"data": []}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting NIBR Biomni Canvas Backend")
    uvicorn.run(app, host="0.0.0.0", port=54367)
