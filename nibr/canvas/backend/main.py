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
import re
from starlette.responses import StreamingResponse
import subprocess
import base64
import io
import sys

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
# Track artifacts per thread
artifacts_db: Dict[str, Dict[str, Any]] = {}

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
            # Handle nested metadata structure from frontend
            if "metadata" in metadata_filter:
                if "user_id" in metadata_filter["metadata"]:
                    user_id = metadata_filter["metadata"]["user_id"]
                    assistants = [a for a in assistants if 
                                a["metadata"].get("user_id") == user_id or
                                a["metadata"].get("user_id") == "system"]
            elif "user_id" in metadata_filter:
                # Direct user_id in filter
                user_id = metadata_filter["user_id"]
                assistants = [a for a in assistants if 
                            a["metadata"].get("user_id") == user_id or
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
            # Handle nested metadata structure from frontend
            if "metadata" in metadata_filter:
                if "supabase_user_id" in metadata_filter["metadata"]:
                    user_id = metadata_filter["metadata"]["supabase_user_id"]
                    threads = [t for t in threads if 
                              t["metadata"].get("supabase_user_id") == user_id or
                              t["metadata"].get("user_id") == user_id]
            elif "supabase_user_id" in metadata_filter:
                # Direct supabase_user_id in filter
                user_id = metadata_filter["supabase_user_id"]
                threads = [t for t in threads if 
                          t["metadata"].get("supabase_user_id") == user_id or
                          t["metadata"].get("user_id") == user_id]
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
    if thread_id in artifacts_db:
        del artifacts_db[thread_id]
    return {"success": True}

# === HELPER FUNCTIONS ===

def should_generate_artifact(prompt: str, has_previous_artifact: bool = False) -> tuple[bool, str, str]:
    """
    Determine if the prompt is asking for code/HTML that should be an artifact.
    Returns (should_generate, artifact_type, language)
    """
    prompt_lower = prompt.lower()
    
    # Check for modification requests when there's a previous artifact
    if has_previous_artifact:
        modification_patterns = [
            r'\b(change|modify|update|edit|adjust|fix|improve|alter|revise)\s+.*\b(code|script|html|it|this)\b',
            r'\bplease\s+(change|modify|update|edit|adjust|fix|improve)\b',
            r'\b(make|so)\s+(it|the|that)\b',
            r'\b(increment|decrement|button|value|counter)\b.*\b(by|of|to)\b',
        ]
        for pattern in modification_patterns:
            if re.search(pattern, prompt_lower):
                # Return True with 'code' type and 'html' as default (will be overridden from context)
                return True, 'code', 'html'
    
    # Check for code/HTML requests
    code_patterns = [
        (r'\b(write|create|generate|make|build)\s+.*\b(html|webpage|website|page)\b', 'code', 'html'),
        (r'\bhtml\s+(with|that|code|example|button|form)\b', 'code', 'html'),
        (r'\bhtml\b.*\b(button|count|increment)\b', 'code', 'html'),  # More specific for button/count
        (r'\b(write|create|generate|make)\s+.*\b(python|javascript|js|typescript|code)\b', 'code', 'python'),
        (r'\b(python|javascript|typescript)\s+(code|script|function|program)\b', 'code', 'python'),
        (r'\bcode\s+(for|that|to)\b', 'code', 'python'),
    ]
    
    for pattern, artifact_type, language in code_patterns:
        if re.search(pattern, prompt_lower):
            # Adjust language based on specific mentions
            if 'javascript' in prompt_lower or 'js' in prompt_lower:
                language = 'javascript'
            elif 'typescript' in prompt_lower:
                language = 'typescript'
            elif 'python' in prompt_lower:
                language = 'python'
            elif 'html' in prompt_lower:
                language = 'html'
            return True, artifact_type, language
    
    # Check for text document requests
    text_patterns = [
        r'\b(write|create|draft|compose)\s+.*\b(letter|document|essay|article|report)\b',
        r'\b(resignation|cover|recommendation)\s+letter\b',
    ]
    
    for pattern in text_patterns:
        if re.search(pattern, prompt_lower):
            return True, 'text', 'other'
    
    return False, '', ''

def extract_title_from_prompt(prompt: str) -> str:
    """Extract a short title from the user's prompt."""
    # Remove common words and get first few significant words
    words = prompt.split()
    significant_words = [w for w in words if len(w) > 3 and w.lower() not in 
                         ['write', 'create', 'make', 'build', 'with', 'that', 'this', 'please']]
    return ' '.join(significant_words[:3]) if significant_words else 'Artifact'

def strip_markdown_code_blocks(content: str) -> str:
    """
    Strip markdown code block wrappers from content.
    Handles various formats like ```html, ```javascript, ```python, etc.
    """
    # Pattern to match markdown code blocks with optional language specifier
    # Matches ```language (or just ```) at the start and ``` at the end
    pattern = r'^```[a-zA-Z0-9]*\n?(.*?)\n?```$'
    
    # Try to match the pattern
    match = re.match(pattern, content.strip(), re.DOTALL)
    
    if match:
        # Return the content without the markdown wrapper
        return match.group(1).strip()
    
    # If no markdown wrapper found, return original content
    return content

# === RUN ENDPOINTS ===

@app.post("/threads/{thread_id}/runs")
def create_run(thread_id: str, run_request: Dict[str, Any]):
    """Create and stream a run"""
    if thread_id not in threads_db:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Log the raw request for debugging
    print(f"📥 Raw request: {json.dumps(run_request, indent=2)}")
    
    # Extract assistant_id and input from request
    assistant_id = run_request.get("assistant_id", "nibr_biomni_default")
    user_input = ""
    
    # Extract user input from various possible formats
    if "input" in run_request:
        input_data = run_request["input"]
        print(f"📋 Input data type: {type(input_data)}")
        print(f"📋 Input data keys: {input_data.keys() if isinstance(input_data, dict) else 'N/A'}")
        
        # Handle nested input structure from Canvas
        if isinstance(input_data, dict) and "input" in input_data:
            # Canvas sends input.input.messages structure
            nested_input = input_data["input"]
            print(f"📋 Found nested input structure, extracting from nested level")
            
            if isinstance(nested_input, dict):
                # Try messages array first (most common)
                if "messages" in nested_input and nested_input["messages"]:
                    messages = nested_input["messages"]
                    # Get the last user message
                    for msg in reversed(messages):
                        if isinstance(msg, dict):
                            if msg.get("role") == "user" and "content" in msg:
                                user_input = msg["content"]
                                break
                            elif "content" in msg:
                                user_input = msg["content"]
                                break
                # Fallback to _messages if messages didn't work
                elif "_messages" in nested_input and nested_input["_messages"]:
                    messages = nested_input["_messages"]
                    for msg in reversed(messages):
                        if isinstance(msg, dict):
                            if msg.get("role") == "user" and "content" in msg:
                                user_input = msg["content"]
                                break
        
        # If still no input, try the direct structure
        elif isinstance(input_data, dict):
            # Check for direct content first
            if "content" in input_data:
                user_input = input_data["content"]
            # Then check for messages array
            elif "messages" in input_data and input_data["messages"]:
                # Get last message content
                last_msg = input_data["messages"][-1]
                if isinstance(last_msg, dict):
                    if "content" in last_msg:
                        user_input = last_msg["content"]
                    elif "text" in last_msg:
                        user_input = last_msg["text"]
                elif isinstance(last_msg, str):
                    user_input = last_msg
            # Check for text field
            elif "text" in input_data:
                user_input = input_data["text"]
        elif isinstance(input_data, str):
            user_input = input_data
        elif isinstance(input_data, list) and input_data:
            # If it's a list of messages, get the last one
            last_msg = input_data[-1]
            if isinstance(last_msg, dict):
                user_input = last_msg.get("content", last_msg.get("text", ""))
            elif isinstance(last_msg, str):
                user_input = last_msg
    
    if not user_input:
        user_input = "Hello! How can I help you today?"
    
    print(f"🎯 Extracted user input: '{user_input}'")
    
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
            # Send initial event to indicate streaming has started
            run_id = str(uuid.uuid4())
            message_id = str(uuid.uuid4())  # Generate a message ID for this response
            yield f"event: message\ndata: {json.dumps({'event': 'on_chain_start', 'run_id': run_id})}\n\n"
            
            # Check if this should generate an artifact
            has_previous_artifact = thread_id in artifacts_db
            should_artifact, artifact_type, language = should_generate_artifact(user_input, has_previous_artifact)
            
            # If modifying an existing artifact, use its language
            if should_artifact and has_previous_artifact:
                previous_artifact = artifacts_db[thread_id]
                language = previous_artifact.get('language', language)
                artifact_type = previous_artifact.get('type', artifact_type)
                print(f"🔧 Modification detected - using previous artifact settings: type={artifact_type}, language={language}")
            
            # Try ChatGPT if available, otherwise use mock response
            if openai_client and OPENAI_API_KEY:
                model_name = "gpt-3.5-turbo"
                print(f"🤖 Using ChatGPT model: {model_name}")
                print(f"📤 Sending prompt: '{user_input}'")
                print(f"🎨 Generate artifact: {should_artifact}, type: {artifact_type}, language: {language}")
                
                # Build message history for context
                chat_messages = []
                
                # Check if user is asking to modify existing artifact
                is_modification = any(word in user_input.lower() for word in 
                                    ['change', 'modify', 'update', 'edit', 'adjust', 'fix', 'improve', 'alter', 'revise',
                                     'make it', 'make the', 'so the', 'so that', 'instead'])
                
                # Also check if talking about the code/artifact specifically
                refers_to_code = any(word in user_input.lower() for word in 
                                    ['the code', 'the script', 'the html', 'it', 'this', 'that'])
                
                # Adjust system prompt based on whether we need an artifact
                if should_artifact:
                    if has_previous_artifact and (is_modification or refers_to_code):
                        # For modifications, be clear about outputting only code
                        if language == 'html':
                            system_prompt = "You are a helpful AI assistant. When modifying HTML code, output ONLY the complete, valid HTML code with proper structure. Do not include any explanations or markdown formatting."
                        else:
                            system_prompt = f"You are a helpful AI assistant. When modifying {language} code, output ONLY the complete {language} code. Do not include any explanations or markdown formatting."
                    elif artifact_type == 'code' and language == 'html':
                        system_prompt = "You are a helpful AI assistant. Generate complete, valid HTML code with proper structure. Include DOCTYPE, html, head, and body tags."
                    elif artifact_type == 'code':
                        system_prompt = f"You are a helpful AI assistant. Generate clean, well-commented {language} code."
                    else:
                        system_prompt = "You are a helpful AI assistant. Generate well-formatted text documents."
                else:
                    system_prompt = "You are a helpful AI assistant for biomedical research at NIBR. Be concise but informative."
                
                chat_messages.append({"role": "system", "content": system_prompt})
                
                # Add previous context if it's a modification request or refers to existing code
                if (is_modification or refers_to_code) and thread_id in artifacts_db:
                    last_artifact = artifacts_db[thread_id]
                    print(f"🔄 Detected modification request. Including previous artifact as context")
                    print(f"📋 Previous artifact type: {last_artifact['type']}, language: {last_artifact['language']}")
                    # Add the previous artifact as context
                    context_msg = f"Here is the current {last_artifact['language']} code that needs to be modified:\n\n```{last_artifact['language']}\n{last_artifact['content']}\n```"
                    chat_messages.append({"role": "assistant", "content": context_msg})
                    
                    # Include last few messages for context (limit to avoid token overflow)
                    if thread_id in messages_db:
                        recent_messages = messages_db[thread_id][-4:]  # Last 4 messages
                        for msg in recent_messages:
                            if msg["type"] == "human":
                                chat_messages.append({"role": "user", "content": msg["content"]})
                            elif msg["type"] == "ai" and "artifact" not in msg:
                                # Only include non-artifact AI responses
                                chat_messages.append({"role": "assistant", "content": msg["content"]})
                
                # Add current user message
                chat_messages.append({"role": "user", "content": user_input})
                
                # Call ChatGPT
                completion = openai_client.chat.completions.create(
                    model=model_name,
                    messages=chat_messages,
                    stream=True
                )
                
                full_response = ""
                chunk_count = 0
                
                if should_artifact:
                    # For artifacts, we need to accumulate the full response first
                    # then send it as a tool call
                    for chunk in completion:
                        if chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_response += content
                            chunk_count += 1
                            print(f"📨 Accumulating chunk {chunk_count}: {repr(content[:50])}")
                    
                    # Send as artifact tool call
                    artifact_title = extract_title_from_prompt(user_input)
                    # Strip markdown code blocks from the response
                    cleaned_content = strip_markdown_code_blocks(full_response)
                    print(f"🎨 Preparing artifact: type={artifact_type}, language={language}, title={artifact_title}")
                    print(f"📝 Original content length: {len(full_response)} chars")
                    print(f"📝 Cleaned content length: {len(cleaned_content)} chars")
                    
                    tool_call_event = {
                        'event': 'on_chat_model_stream',
                        'run_id': run_id,
                        'data': {
                            'chunk': {
                                'id': message_id,
                                'content': '',
                                'type': 'AIMessageChunk',
                                'tool_call_chunks': [{
                                    'name': 'generate_artifact',
                                    'args': json.dumps({
                                        'type': artifact_type,
                                        'language': language,
                                        'artifact': cleaned_content,
                                        'title': artifact_title
                                    }),
                                    'id': str(uuid.uuid4()),
                                    'index': 0
                                }]
                            }
                        }
                    }
                    
                    event_str = f"event: message\ndata: {json.dumps(tool_call_event)}\n\n"
                    print(f"🚀 Yielding artifact event, size: {len(event_str)} bytes")
                    yield event_str
                    await asyncio.sleep(0.1)  # Give time for the event to be sent
                    print(f"✅ Artifact event sent successfully")
                else:
                    # Regular streaming for non-artifact responses
                    for chunk in completion:
                        if chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_response += content
                            chunk_count += 1
                            
                            # Log each chunk
                            print(f"📨 Chunk {chunk_count}: {repr(content)}")
                            
                            # Send SSE formatted event with message structure
                            event_data = {
                                'event': 'on_chat_model_stream',  # Canvas expects this event name
                                'run_id': run_id,
                                'data': {
                                    'chunk': {
                                        'id': message_id,
                                        'content': content,
                                        'type': 'AIMessageChunk'
                                    }
                                }
                            }
                            yield f"event: message\ndata: {json.dumps(event_data)}\n\n"
                            await asyncio.sleep(0.01)
                
                print(f"✅ ChatGPT response complete. Total chunks: {chunk_count}")
                print(f"📝 Full response: '{full_response}'")
                
                # Add assistant message to thread
                assistant_message = {
                    "id": str(uuid.uuid4()),
                    "type": "ai",
                    "content": full_response,
                    "created_at": datetime.datetime.utcnow().isoformat(),
                }
                # Store artifact info if this was an artifact
                if should_artifact:
                    assistant_message["artifact"] = {
                        "type": artifact_type,
                        "language": language,
                        "content": cleaned_content,
                        "title": artifact_title
                    }
                    # Store in artifacts_db for easy access
                    artifacts_db[thread_id] = assistant_message["artifact"]
                messages_db[thread_id].append(assistant_message)
                        
            else:
                print("🎭 Using mock response (no OpenAI API key)")
                print(f"📤 Processing prompt: '{user_input}'")
                
                # Fallback mock response
                mock_response = f"Thank you for your message: '{user_input}'. This is a mock response from the NIBR Biomni Canvas backend. In Phase 2, this will be powered by real Biomni agents with access to biomedical research data and tools."
                
                # Stream the mock response word by word
                words = mock_response.split()
                full_response = ""
                chunk_count = 0
                for word in words:
                    full_response += word + " "
                    chunk_count += 1
                    
                    # Log each chunk
                    print(f"📨 Mock chunk {chunk_count}: '{word} '")
                    
                    # Send SSE formatted event with message structure
                    event_data = {
                        'event': 'on_chat_model_stream',  # Canvas expects this event name
                        'run_id': run_id,
                        'data': {
                            'chunk': {
                                'id': message_id,
                                'content': word + " ",
                                'type': 'AIMessageChunk'
                            }
                        }
                    }
                    yield f"event: message\ndata: {json.dumps(event_data)}\n\n"
                    await asyncio.sleep(0.1)
                
                print(f"✅ Mock response complete. Total chunks: {chunk_count}")
                print(f"📝 Full response: '{full_response.strip()}'")
                
                # Add assistant message to thread
                assistant_message = {
                    "id": str(uuid.uuid4()),
                    "type": "ai", 
                    "content": full_response.strip(),
                    "created_at": datetime.datetime.utcnow().isoformat(),
                }
                messages_db[thread_id].append(assistant_message)
            
            # Send final event (empty output for artifacts to avoid duplication)
            if should_artifact:
                # For artifacts, don't send the content again in chain_end
                final_event = {
                    'event': 'on_chain_end',
                    'run_id': run_id,
                    'data': {
                        'output': ''  # Empty for artifacts
                    }
                }
            else:
                # For regular messages, include the content
                final_event = {
                    'event': 'on_chain_end',
                    'run_id': run_id,
                    'data': {
                        'output': messages_db[thread_id][-1]['content'] if messages_db[thread_id] else ''
                    }
                }
            yield f"event: message\ndata: {json.dumps(final_event)}\n\n"
                        
        except Exception as e:
            print(f"❌ Error in streaming: {e}")
            error_event = {
                'event': 'error',
                'data': {
                    'message': str(e)
                }
            }
            yield f"event: error\ndata: {json.dumps(error_event)}\n\n"

    return StreamingResponse(generate_response(), media_type="text/event-stream")

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

# === CODE EXECUTION ENDPOINTS ===

class PythonExecuteRequest(BaseModel):
    code: str

class PythonExecuteResponse(BaseModel):
    output: Optional[str] = None
    error: Optional[str] = None
    plots: Optional[List[str]] = None
    tables: Optional[List[Any]] = None

@app.post("/api/execute/python", response_model=PythonExecuteResponse)
async def execute_python(request: PythonExecuteRequest):
    """Execute Python code in a sandboxed environment"""
    try:
        # Create a temporary Python file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Add imports for capturing output
            setup_code = """
import sys
import io
import json
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO

_captured_plots = []
_captured_tables = []
_original_show = plt.show

def _capture_show():
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    _captured_plots.append(base64.b64encode(buf.read()).decode('utf-8'))
    plt.clf()

plt.show = _capture_show

# Capture stdout
_stdout = io.StringIO()
_original_stdout = sys.stdout
sys.stdout = _stdout

try:
"""
            cleanup_code = """
finally:
    # Restore stdout
    sys.stdout = _original_stdout
    output = _stdout.getvalue()
    
    # Save any remaining plots
    if plt.get_fignums():
        _capture_show()
    
    # Print results as JSON
    import json
    result = {
        'output': output,
        'plots': _captured_plots,
        'tables': _captured_tables
    }
    print('###RESULT###')
    print(json.dumps(result))
"""
            
            # Indent the user code
            indented_code = '\n'.join('    ' + line for line in request.code.split('\n'))
            
            full_code = setup_code + indented_code + cleanup_code
            f.write(full_code)
            temp_file = f.name
        
        # Execute the Python code with timeout
        try:
            # Use subprocess to run in isolated environment
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                check=False
            )
            
            # Parse the output
            output_text = result.stdout
            error_text = result.stderr
            
            # Extract JSON result if present
            if '###RESULT###' in output_text:
                parts = output_text.split('###RESULT###')
                if len(parts) > 1:
                    try:
                        json_result = json.loads(parts[1].strip())
                        return PythonExecuteResponse(
                            output=json_result.get('output'),
                            error=error_text if error_text else None,
                            plots=json_result.get('plots'),
                            tables=json_result.get('tables')
                        )
                    except json.JSONDecodeError:
                        pass
            
            # Fallback if no JSON result
            return PythonExecuteResponse(
                output=output_text if output_text else None,
                error=error_text if error_text else None
            )
            
        except subprocess.TimeoutExpired:
            return PythonExecuteResponse(
                error="Execution timeout (30 seconds)"
            )
        finally:
            # Clean up temp file
            os.unlink(temp_file)
            
    except Exception as e:
        return PythonExecuteResponse(
            error=f"Execution failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting NIBR Biomni Canvas Backend")
    uvicorn.run(app, host="0.0.0.0", port=54367)
