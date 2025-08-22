# NIBR Biomni Canvas - Local Architecture

## Overview

The NIBR Biomni Canvas has been redesigned for **closed environment deployment** without external dependencies like LangGraph Cloud. This ensures all data and processing remains within NIBR's secure infrastructure.

## Architecture Components

### 1. Local Assistant Manager (`/lib/local-assistant-manager.ts`)
- **Purpose**: Pure TypeScript implementation for managing assistants, conversations, and messages
- **Storage**: In-memory with plans for SQLite persistence
- **Features**:
  - Assistant creation and management
  - Thread/conversation handling
  - Message history
  - Run execution tracking

### 2. Local Client (`/lib/local-client.ts`)
- **Purpose**: Mimics LangGraph SDK interface for seamless frontend integration
- **Benefits**: Drop-in replacement for LangGraph SDK without code changes
- **Capabilities**:
  - Assistant CRUD operations
  - Thread management
  - Run execution with streaming support

### 3. Biomni Integration (`/lib/biomni-integration.ts`)
- **Purpose**: Direct integration with Biomni agents
- **Features**:
  - Agent initialization and management
  - Streaming responses
  - Mock research capabilities (literature search, data analysis, visualization)
  - Tool usage tracking

## Security & Compliance

### ✅ **Closed Environment Benefits**
- **No External API Calls**: All processing happens locally
- **Data Privacy**: No data leaves NIBR infrastructure
- **Zero Cloud Dependencies**: Runs entirely on-premises
- **Offline Capable**: Works without internet connection
- **Regulatory Compliance**: Meets pharmaceutical industry standards

### 🔒 **Data Flow**
```
User Input → Local Client → Local Assistant Manager → Biomni Integration → Response
     ↑                                                                          ↓
     └─── Browser UI ←─── Local Storage ←─── In-Memory State ←─── Agent Response
```

## Current Capabilities

### 🧬 **Research Assistant Features**
- **Literature Search**: Simulated PubMed and internal database queries
- **Data Analysis**: Statistical analysis with confidence intervals
- **Visualization**: Chart and plot generation
- **Clinical Insights**: Trial design and regulatory guidance
- **Drug Discovery**: Compound analysis and target identification

### 🛠 **Technical Features**
- **Real-time Streaming**: Progressive response generation
- **Tool Usage Tracking**: Monitor which research tools are employed
- **Artifact Generation**: Create downloadable reports and visualizations
- **Confidence Scoring**: AI confidence levels for research insights
- **Citation Management**: Track and link to relevant publications

## Development vs Production

### Development Mode (Current)
- Mock Biomni responses with realistic research content
- Simulated processing delays
- Example data and citations
- Full UI functionality for testing

### Production Integration (Next Phase)
- Real Biomni agent initialization
- Actual research database connections
- Live literature search APIs
- True statistical analysis engines
- Genuine visualization generation

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  NIBR Secure Infrastructure                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Web Browser   │  │   Canvas UI     │  │   SQLite DB  │ │
│  │   (Frontend)    │→ │   (Next.js)     │→ │   (Local)    │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│            ↓                    ↓                   ↓        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Local Client   │  │ Assistant Mgr   │  │   Biomni     │ │
│  │  (SDK Compat)   │→ │ (Conversations) │→ │   Agents     │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │           NIBR Research Data & Tools                    │ │
│  │  • Internal Publications  • Clinical Trials Data       │ │
│  │  • Compound Databases    • Statistical Tools           │ │
│  │  • Regulatory Guidelines • Analysis Pipelines          │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Next Steps

1. **Test Current Implementation**: Verify UI works with local architecture
2. **Real Biomni Integration**: Replace mock responses with actual agent calls
3. **Persistence Layer**: Add SQLite storage for conversation history
4. **Enhanced Security**: Add encryption and access controls
5. **Performance Optimization**: Cache frequently used research data
6. **Tool Integration**: Connect to real NIBR research databases

## Benefits for NIBR

- **🛡️ Security**: No external data exposure
- **📋 Compliance**: Meets pharmaceutical regulations  
- **⚡ Performance**: Local processing, no network latency
- **🔧 Customization**: Tailored to NIBR research workflows
- **💰 Cost**: No cloud service fees
- **🎯 Control**: Full control over AI models and data

This architecture ensures the Canvas remains within NIBR's secure environment while providing powerful research assistance capabilities.
