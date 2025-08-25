"""
NIBR Biomni Canvas Backend - Phase 1.5
FastAPI backend providing Canvas functionality with ChatGPT integration
Later to be connected to Biomni agents
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, AsyncGenerator
from pydantic import BaseModel
import uuid
import openai
import os
from contextlib import asynccontextmanager

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEVELOPMENT_MODE = os.getenv("NODE_ENV", "development") == "development"

# In-memory storage (for development - later replace with proper database)
assistants_db: Dict[str, Dict] = {}
threads_db: Dict[str, Dict] = {}
runs_db: Dict[str, Dict] = {}
messages_db: Dict[str, List[Dict]] = {}  # thread_id -> messages

# Pydantic models
class Assistant(BaseModel):
    assistant_id: str
    graph_id: str = "agent"
    name: str
    config: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str

class Thread(BaseModel):
    thread_id: str
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]
    values: Dict[str, Any] = {}

class Message(BaseModel):
    id: str
    type: str  # "human" or "ai"
    content: str
    additional_kwargs: Dict[str, Any] = {}
    created_at: str

class RunRequest(BaseModel):
    input: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None
    stream_mode: str = "events"

class AssistantCreate(BaseModel):
    name: str
    graph_id: str = "agent"
    config: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

class AssistantSearch(BaseModel):
    metadata: Optional[Dict[str, Any]] = None
    limit: Optional[int] = 100

# Initialize OpenAI client
openai_client = None
if OPENAI_API_KEY:
    openai_client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting NIBR Biomni Canvas Backend")
    
    # Initialize default assistant
    default_assistant = {
        "assistant_id": "nibr_biomni_default",
        "graph_id": "agent",
        "name": "NIBR Biomni Assistant",
        "config": {
            "configurable": {
                "systemPrompt": """You are the NIBR Biomni Assistant, a specialized research AI for biomedical and pharmaceutical research.

Your capabilities include:
- Biomedical literature search and analysis
- Drug discovery and development insights
- Clinical trial data interpretation
- Molecular structure analysis
- Research methodology guidance
- Scientific data visualization
- Regulatory compliance information

You have access to NIBR's internal research data and tools. Always maintain confidentiality and follow NIBR research guidelines.""",
                "tools": ["biomni_search", "biomni_analyze", "biomni_visualize", "literature_search"],
                "temperature": 0.1,
                "model": "gpt-4"
            }
        },
        "metadata": {
            "user_id": "system",
            "is_default": True,
            "iconName": "Bot",
            "iconColor": "#0066cc",
            "description": "Your NIBR Biomni research assistant with access to internal research tools and data.",
            "created_by": "system"
        },
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    assistants_db[default_assistant["assistant_id"]] = default_assistant
    
    yield
    # Shutdown
    print("🛑 Shutting down NIBR Biomni Canvas Backend")

# Create FastAPI app
app = FastAPI(
    title="NIBR Biomni Canvas Backend",
    description="Backend API for NIBR Biomni Canvas - Phase 1.5",
    version="1.5.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.5.0",
        "mode": "development" if DEVELOPMENT_MODE else "production"
    }

async def search_assistants_impl(metadata: str = None, limit: int = 100):
    """Implementation for searching assistants"""
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
    
    # Sort by creation date (newest first)
    assistants.sort(key=lambda x: x["created_at"], reverse=True)
    
    return assistants[:limit]

# Assistant endpoints
@app.get("/assistants")
async def search_assistants(metadata: str = None, limit: int = 100):
    """Search assistants with optional metadata filtering"""
    return await search_assistants_impl(metadata, limit)

# Remove LangGraph compatibility endpoints - we don't need them anymore

@app.get("/assistants/{assistant_id}")
async def get_assistant(assistant_id: str):
    """Get specific assistant by ID"""
    if assistant_id not in assistants_db:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return assistants_db[assistant_id]

@app.post("/assistants")
async def create_assistant(assistant: AssistantCreate):
    """Create new assistant"""
    assistant_id = f"assistant_{uuid.uuid4().hex[:8]}"
    now = datetime.utcnow().isoformat()
    
    new_assistant = {
        "assistant_id": assistant_id,
        "graph_id": assistant.graph_id,
        "name": assistant.name,
        "config": assistant.config,
        "metadata": assistant.metadata,
        "created_at": now,
        "updated_at": now
    }
    
    assistants_db[assistant_id] = new_assistant
    return new_assistant

@app.put("/assistants/{assistant_id}")
async def update_assistant(assistant_id: str, updates: Dict[str, Any]):
    """Update assistant"""
    if assistant_id not in assistants_db:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    assistant = assistants_db[assistant_id]
    assistant.update(updates)
    assistant["updated_at"] = datetime.utcnow().isoformat()
    
    return assistant

@app.delete("/assistants/{assistant_id}")
async def delete_assistant(assistant_id: str):
    """Delete assistant"""
    if assistant_id not in assistants_db:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    del assistants_db[assistant_id]
    return {"success": True}

# Thread endpoints
@app.post("/threads")
async def create_thread(metadata: Dict[str, Any] = {}):
    """Create new thread"""
    thread_id = f"thread_{uuid.uuid4().hex}"
    now = datetime.utcnow().isoformat()
    
    thread = {
        "thread_id": thread_id,
        "created_at": now,
        "updated_at": now,
        "metadata": metadata,
        "values": {}
    }
    
    threads_db[thread_id] = thread
    messages_db[thread_id] = []
    
    return thread

async def search_threads_impl(metadata: str = None, limit: int = 100):
    """Implementation for searching threads"""
    threads = list(threads_db.values())
    
    if metadata:
        try:
            metadata_filter = json.loads(metadata)
            if "supabase_user_id" in metadata_filter:
                threads = [t for t in threads if 
                          t["metadata"].get("user_id") == metadata_filter["supabase_user_id"]]
        except json.JSONDecodeError:
            pass
    
    # Sort by creation date (newest first)
    threads.sort(key=lambda x: x["created_at"], reverse=True)
    
    return threads[:limit]

@app.get("/threads")
async def search_threads(metadata: str = None, limit: int = 100):
    """Search threads with optional metadata filtering"""
    return await search_threads_impl(metadata, limit)

# Remove LangGraph compatibility endpoints - we don't need them anymore

@app.get("/threads/{thread_id}")
async def get_thread(thread_id: str):
    """Get thread by ID"""
    if thread_id not in threads_db:
        raise HTTPException(status_code=404, detail="Thread not found")
    return threads_db[thread_id]

@app.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str):
    """Delete thread"""
    if thread_id in threads_db:
        del threads_db[thread_id]
    if thread_id in messages_db:
        del messages_db[thread_id]
    return {"success": True}

# Run endpoints - simplified without LangGraph dependencies
@app.post("/threads/{thread_id}/runs")
async def create_run(thread_id: str, run_request: Dict[str, Any]):
    """Create and stream a run with ChatGPT integration"""
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
    
    # Create run record
    run_id = str(uuid.uuid4())
    
    # Store the run (simple in-memory for now)
    if thread_id not in messages_db:
        messages_db[thread_id] = []
    
    # Add user message
    user_message = {
        "id": str(uuid.uuid4()),
        "type": "human",
        "content": user_input,
        "created_at": datetime.utcnow().isoformat()
    }
    messages_db[thread_id].append(user_message)

    async def generate_response():
        try:
            # Try ChatGPT if available, otherwise use mock response
            if openai_client:
                # Call ChatGPT
                completion = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful AI assistant for biomedical research at NIBR."},
                        {"role": "user", "content": user_input}
                    ],
                    stream=True
                )
                
                full_response = ""
                for chunk in completion:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        
                        # Send chunk as plain text
                        yield content
                        await asyncio.sleep(0.01)
                
                # Add assistant message to thread
                assistant_message = {
                    "id": str(uuid.uuid4()),
                    "type": "ai",
                    "content": full_response,
                    "created_at": datetime.utcnow().isoformat(),
                    "run_id": run_id
                }
                messages_db[thread_id].append(assistant_message)
                        
            else:
                # Fallback mock response
                mock_response = f"Thank you for your message: '{user_input}'. This is a mock response from the NIBR Biomni Canvas backend. In Phase 2, this will be powered by real Biomni agents with access to biomedical research data and tools."
                
                # Stream the mock response word by word
                words = mock_response.split()
                full_response = ""
                for word in words:
                    full_response += word + " "
                    yield word + " "
                    await asyncio.sleep(0.1)  # Simulate typing
                
                # Add assistant message to thread
                assistant_message = {
                    "id": str(uuid.uuid4()),
                    "type": "ai", 
                    "content": full_response.strip(),
                    "created_at": datetime.utcnow().isoformat(),
                    "run_id": run_id
                }
                messages_db[thread_id].append(assistant_message)
                        
        except Exception as e:
            print(f"Error in streaming: {e}")
            yield f"Error: {str(e)}"

    return StreamingResponse(generate_response(), media_type="text/plain")

# === STORE API ENDPOINTS FOR FRONTEND COMPATIBILITY ===
    """Create and stream a run"""
    if thread_id not in threads_db:
        raise HTTPException(status_code=404, detail="Thread not found")
    if assistant_id not in assistants_db:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    async def stream_generator():
        run_id = f"run_{thread_id}_{uuid.uuid4().hex[:8]}"
        assistant = assistants_db[assistant_id]
        
        try:
            # Add human message
            human_message = run_request.input.get("messages", [{}])[-1]
            human_content = human_message.get("content", "Hello")
            
            # Add to messages
            human_msg = {
                "id": f"msg_{uuid.uuid4().hex[:8]}",
                "type": "human",
                "content": human_content,
                "additional_kwargs": {},
                "created_at": datetime.utcnow().isoformat()
            }
            messages_db[thread_id].append(human_msg)
            
            # Yield human message event
            yield f"data: {json.dumps({'event': 'on_chat_model_stream', 'data': {'chunk': human_msg}})}\n\n"
            
            # Generate AI response using OpenAI or mock
            if openai_client and OPENAI_API_KEY:
                ai_content = await generate_openai_response(human_content, assistant)
            else:
                ai_content = await generate_mock_response(human_content, assistant)
            
            # Stream AI response in chunks
            words = ai_content.split(" ")
            current_chunk = ""
            
            for i, word in enumerate(words):
                current_chunk += word + " "
                
                # Yield chunk every few words
                if i % 3 == 0 or i == len(words) - 1:
                    await asyncio.sleep(0.1)  # Simulate streaming delay
                    yield f"data: {json.dumps({'event': 'on_chat_model_stream', 'data': {'chunk': {'type': 'AIMessageChunk', 'content': current_chunk.strip(), 'additional_kwargs': {}}}})}\n\n"
                    current_chunk = ""
            
            # Add complete AI message
            ai_msg = {
                "id": f"msg_{uuid.uuid4().hex[:8]}",
                "type": "ai", 
                "content": ai_content,
                "additional_kwargs": {
                    "model": assistant["config"]["configurable"].get("model", "gpt-4"),
                    "confidence": 0.95,
                    "processing_time": "2.1s"
                },
                "created_at": datetime.utcnow().isoformat()
            }
            messages_db[thread_id].append(ai_msg)
            
            # Yield completion event
            yield f"data: {json.dumps({'event': 'on_chat_model_end', 'data': {'output': ai_msg}})}\n\n"
            
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            yield f"data: {json.dumps({'event': 'on_chat_model_error', 'data': {'error': error_msg}})}\n\n"
    
    return StreamingResponse(stream_generator(), media_type="text/plain")

async def generate_openai_response(user_message: str, assistant: Dict) -> str:
    """Generate response using OpenAI"""
    try:
        system_prompt = assistant["config"]["configurable"].get("systemPrompt", "You are a helpful assistant.")
        
        response = await openai_client.chat.completions.create(
            model=assistant["config"]["configurable"].get("model", "gpt-4"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=assistant["config"]["configurable"].get("temperature", 0.1),
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"I apologize, but I encountered an error: {str(e)}. Please try again."

async def generate_mock_response(user_message: str, assistant: Dict) -> str:
    """Generate mock response for development"""
    await asyncio.sleep(1)  # Simulate processing time
    
    if "poem" in user_message.lower() and "ai" in user_message.lower():
        return """Here's a poem about AI:

**Digital Dreams**

In circuits deep and data streams,  
Where silicon minds weave digital dreams,  
A new intelligence takes its form,  
Beyond the bounds of human norm.

Through algorithms swift and bright,  
We glimpse the future's guiding light,  
Where man and machine in harmony dance,  
Creating tomorrow's vast expanse.

With knowledge vast and learning true,  
AI opens pathways fresh and new,  
A tool to heal, to build, to grow,  
And help humanity's wisdom flow.

*Generated by NIBR Biomni Assistant - bridging research and innovation.*"""
    
    return f"""Hello! I'm the {assistant['name']}. I received your message: "{user_message}"

I'm ready to help you with:
• **Biomedical Research**: Literature searches and analysis
• **Drug Discovery**: Compound analysis and target identification  
• **Clinical Insights**: Trial design and regulatory guidance
• **Data Analysis**: Statistical analysis and interpretation
• **Visualization**: Create charts and interactive plots

*Note: I'm currently running with OpenAI integration. The full Biomni framework integration is planned for the next phase.*

What specific research question can I help you with today?"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=54367)
