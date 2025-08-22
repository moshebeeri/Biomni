# NIBR Biomni Canvas - No LangGraph Architecture

## 🎯 **Architecture Overview**

We have successfully **removed all LangGraph dependencies** and created a clean, pure FastAPI + OpenAI backend that directly serves the Canvas frontend.

### **Key Components:**

1. **Pure FastAPI Backend** (`backend/main.py`)
   - No LangGraph SDK dependencies
   - Direct OpenAI ChatGPT integration
   - Simple in-memory storage for development
   - Clean REST API endpoints

2. **Canvas Client** (`apps/web/src/lib/canvas-client.ts`)
   - Direct HTTP client using native `fetch`
   - No external SDK dependencies
   - Simple, focused interface

3. **Compatibility Layer** (`apps/web/src/lib/langchain-compat.ts`)
   - Provides LangGraph SDK-compatible interface
   - Uses CanvasClient under the hood
   - Allows existing frontend code to work unchanged

4. **Frontend Integration** (`apps/web/src/hooks/utils.ts`)
   - Uses compatibility layer instead of LangGraph SDK
   - Transparent to the rest of the application

## 🔄 **Data Flow**

```
Frontend (React) 
    ↓ (createClient)
Compatibility Layer 
    ↓ (HTTP calls)
Canvas Client 
    ↓ (fetch API)
FastAPI Backend 
    ↓ (OpenAI API)
ChatGPT
```

## 🚀 **Current Capabilities**

- ✅ **Pure FastAPI backend** - No LangGraph dependencies
- ✅ **ChatGPT integration** - Direct OpenAI API calls
- ✅ **Streaming responses** - Real-time text streaming
- ✅ **Assistant management** - Create, update, delete assistants
- ✅ **Thread management** - Conversation persistence
- ✅ **Mock authentication** - Development accounts
- ✅ **CORS configured** - Frontend/backend communication
- ✅ **Compatibility layer** - Existing frontend code works

## 📊 **API Endpoints**

### Assistants
- `GET /assistants` - List all assistants
- `GET /assistants/{id}` - Get specific assistant
- `POST /assistants` - Create new assistant
- `PUT /assistants/{id}` - Update assistant
- `DELETE /assistants/{id}` - Delete assistant

### Threads
- `GET /threads` - List all threads
- `GET /threads/{id}` - Get specific thread
- `POST /threads` - Create new thread
- `PUT /threads/{id}` - Update thread
- `DELETE /threads/{id}` - Delete thread

### Runs (Chat)
- `POST /threads/{id}/runs` - Start conversation (streaming)

### Store (Frontend compatibility)
- `POST /store/get` - Mock data retrieval
- `POST /store/insert` - Mock data insertion
- `POST /store/update` - Mock data update
- `POST /store/delete` - Mock data deletion

## 🏗️ **Development Setup**

1. **Backend**: `python start_backend.py` (Port 54367)
2. **Frontend**: `npm run dev` (Port 3000/3001/3002)
3. **Authentication**: Mock accounts (admin@example.com/admin)

## 🎭 **ChatGPT vs Mock Responses**

- **With OPENAI_API_KEY**: Uses real ChatGPT responses
- **Without API key**: Uses mock responses for development

## 🔮 **Phase 2: Biomni Integration**

The next phase will replace the ChatGPT integration with real Biomni agents:

```python
# Future: backend/main.py
from biomni.agent import A1
from biomni.persistent import PersistentA1, GlobalAgentManager

# Replace ChatGPT calls with Biomni agent execution
agent = GlobalAgentManager.get_agent("research_assistant")
response = await agent.execute(user_input)
```

## 📝 **Benefits of This Architecture**

1. **No External Dependencies**: No LangGraph, LangChain, or other complex SDKs
2. **Direct Control**: Full control over API responses and behavior
3. **Simple Debugging**: Easy to trace requests and responses
4. **Performance**: No middleware overhead from external SDKs
5. **Flexibility**: Easy to integrate Biomni agents in Phase 2
6. **Development Friendly**: Mock responses when APIs unavailable

## 🧪 **Testing**

```bash
# Test backend health
curl http://localhost:54367/health

# Test assistants
curl http://localhost:54367/assistants

# Test frontend
open http://localhost:3002
# Login: admin@example.com / admin
# Try: "Write a poem about AI"
```

This architecture provides a clean foundation for integrating Biomni agents while maintaining full compatibility with the existing Canvas frontend!
