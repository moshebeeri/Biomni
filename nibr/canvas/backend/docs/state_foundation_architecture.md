# Pre-Phase 0: State Management Foundation

## Overview

The State Management Foundation solves the **critical statelessness problem** of biomni agents by implementing a comprehensive persistence layer. This foundation enables GenAI assistants to maintain agent state across conversations and provides the infrastructure for collaborative biomedical research workflows.

## Architecture Components

### 1. PersistentA1 Class

**Purpose**: Extends the base `biomni.agent.A1` class with comprehensive state persistence capabilities.

**Key Features**:
- Automatic persistence of custom tools, data, and software
- JSON-based state storage with atomic writes
- Advanced tool serialization using `dill` and `cloudpickle`
- Enhanced `add_software` with actual package installation
- State export/import for collaboration
- Auto-save functionality with dirty state tracking

**Architecture**:
```python
class PersistentA1(A1):
    """Extended A1 with state persistence"""
    
    # Core persistence methods
    def _save_persistent_state()     # Atomic JSON state saving
    def _load_persistent_state()     # State restoration on init
    def _serialize_custom_tools()    # Advanced tool serialization
    
    # Enhanced API methods (with persistence)
    def add_tool(api: Callable)      # Adds tool + persists state
    def add_data(data: Dict)         # Adds data + persists state  
    def add_software(software: Dict, install: bool)  # Enhanced with actual installation
    
    # State management
    def export_state(path: str)      # Export for sharing
    def import_state(path: str)      # Import from export
    def get_state_summary()          # Current state overview
```

### 2. ToolSerializationEngine

**Purpose**: Robust serialization/deserialization of Python functions for persistence.

**Serialization Strategy**:
1. **Primary**: `dill` serialization (handles closures, complex functions)
2. **Fallback**: Source code extraction with `inspect.getsource()`
3. **Last resort**: Metadata-only storage

**Features**:
- Handles complex functions with closures
- Preserves function metadata (docstrings, annotations)
- Graceful degradation when serialization fails
- Version tracking for compatibility

### 3. GlobalAgentManager

**Purpose**: Singleton service for managing persistent agent instances across Canvas sessions.

**Key Capabilities**:
- Agent lifecycle management (create, get, delete)
- Memory management with cleanup policies
- Agent cloning for collaboration
- Cross-session persistence
- State file management

**Architecture**:
```python
class GlobalAgentManager:
    """Singleton agent manager"""
    
    # Agent lifecycle
    def create_agent(agent_id: str, **kwargs) -> PersistentA1
    def get_agent(agent_id: str) -> PersistentA1
    def delete_agent(agent_id: str, remove_files: bool)
    
    # Collaboration
    def clone_agent(source_id: str, target_id: str) -> PersistentA1
    def list_agents() -> List[str]
    def get_agent_summary(agent_id: str) -> Dict
    
    # Maintenance
    def cleanup_unused_agents(max_idle_hours: int) -> int
```

## State Persistence Model

### Directory Structure
```
./data/agents/
├── states/
│   ├── researcher_001.json          # Agent state file
│   ├── researcher_002.json
│   └── tools/
│       ├── researcher_001/          # Tool-specific data
│       └── researcher_002/
└── data/
    ├── researcher_001/              # Agent-specific data files
    └── researcher_002/
```

### State File Format
```json
{
  "agent_id": "researcher_001",
  "timestamp": "2024-01-15T10:30:00Z",
  "agent_config": {
    "llm": "claude-3-5-sonnet-20241022",
    "use_tool_retriever": true,
    "timeout_seconds": 600
  },
  "custom_tools": {
    "analyze_protein": {
      "name": "analyze_protein",
      "doc": "Analyze protein sequence",
      "serialization_method": "dill",
      "serialized_data": "base64_encoded_function",
      "timestamp": "2024-01-15T10:25:00Z"
    }
  },
  "custom_data": {
    "lab_data.csv": "Lab experimental results",
    "literature.json": "Cached literature search"
  },
  "custom_software": {
    "biopython": "Bioinformatics library",
    "pip:networkx": "Network analysis"
  },
  "version": "1.0"
}
```

## Enhanced add_software Implementation

The original biomni `add_software` only adds metadata. Our enhanced version provides **actual installation**:

```python
def add_software(self, software: Dict[str, str], install: bool = False):
    """Enhanced add_software with actual package installation."""
    
    # Original behavior - add metadata
    super().add_software(software)
    
    # New capability - actual installation
    if install:
        for package_spec, description in software.items():
            if package_spec.startswith("pip:"):
                # Install via pip
                subprocess.run([sys.executable, "-m", "pip", "install", package])
            elif package_spec.startswith("conda:"):
                # Install via conda
                subprocess.run(["conda", "install", "-y", package])
            elif package_spec.startswith("r:"):
                # Install R package
                subprocess.run(["Rscript", "-e", f'install.packages("{package}")'])
```

**Usage**:
```python
agent.add_software({
    "pip:pandas": "Data manipulation library",
    "conda:scikit-learn": "Machine learning library", 
    "r:ggplot2": "R plotting library"
}, install=True)
```

## Integration with Canvas

### WebSocket API Integration
```python
# Canvas adapter integration
from biomni.persistent_agent import agent_manager

@app.websocket("/ws/research/{session_id}")
async def research_websocket(websocket: WebSocket, session_id: str):
    # Get persistent agent for user
    user_id = get_user_from_session(session_id)
    agent = agent_manager.get_agent(f"canvas_user_{user_id}")
    
    # Execute tasks with state preservation
    async for update in agent.go_stream(prompt):
        await websocket.send_json(update)
```

### REST API Extensions
```python
@app.post("/api/agent/create")
async def create_persistent_agent(agent_config: dict):
    agent = agent_manager.create_agent(
        agent_id=agent_config['agent_id'],
        **agent_config['settings']
    )
    return {"status": "created", "agent_id": agent.agent_id}

@app.get("/api/agent/{agent_id}/state")
async def get_agent_state(agent_id: str):
    agent = agent_manager.get_agent(agent_id)
    return agent.get_state_summary()

@app.post("/api/agent/{agent_id}/export")
async def export_agent_state(agent_id: str, export_path: str):
    agent = agent_manager.get_agent(agent_id)
    agent.export_state(export_path)
    return {"status": "exported", "path": export_path}
```

## Collaboration Patterns

### Agent Cloning for Team Collaboration
```python
# Research team leader sets up base agent
leader_agent = agent_manager.create_agent("team_leader_genomics")
leader_agent.add_tool(genomics_analysis_pipeline)
leader_agent.add_data(shared_datasets)

# Clone for team members
member1_agent = agent_manager.clone_agent("team_leader_genomics", "member1_genomics") 
member2_agent = agent_manager.clone_agent("team_leader_genomics", "member2_genomics")

# Members can extend with their specific tools
member1_agent.add_tool(protein_structure_analysis)
member2_agent.add_tool(drug_target_prediction)
```

### Cross-Domain Collaboration
```python
# Genomics researcher shares findings with drug discovery team
genomics_agent = agent_manager.get_agent("genomics_researcher_001")
drug_agent = agent_manager.get_agent("drug_discovery_researcher_001")

# Export genomics state
genomics_agent.export_state("/shared/genomics_findings.json")

# Import into drug discovery agent (merge mode)
drug_agent.import_state("/shared/genomics_findings.json", merge=True)
```

## Performance Characteristics

### Memory Management
- **In-memory caching**: Active agents kept in memory for fast access
- **Lazy loading**: Agents loaded from disk only when needed
- **Automatic cleanup**: Unused agents removed after configurable idle time
- **Memory limits**: Configurable limits on concurrent in-memory agents

### Storage Efficiency
- **Atomic writes**: State files written atomically to prevent corruption
- **Compression**: Large state files can be compressed
- **Incremental saves**: Only changed state components saved
- **Deduplication**: Shared tools/data stored once, referenced by multiple agents

### Scalability
- **Horizontal scaling**: Multiple GlobalAgentManager instances supported
- **Database backends**: SQLite for small deployments, PostgreSQL/Redis for enterprise
- **Microservice ready**: Designed for containerized deployment
- **Load balancing**: Agent requests can be distributed across instances

## Error Handling and Recovery

### State Corruption Protection
```python
def _save_persistent_state(self):
    """Atomic state saving with corruption protection."""
    try:
        # Write to temporary file first
        temp_file = self.state_file.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        # Atomic replace
        temp_file.replace(self.state_file)
        
    except Exception as e:
        logger.error(f"State save failed: {e}")
        # Recovery logic
```

### Graceful Degradation
- **Tool serialization failures**: Fall back to metadata-only storage
- **State file corruption**: Rebuild from last known good state
- **Package installation failures**: Continue with metadata, log errors
- **Memory exhaustion**: Evict least recently used agents

## Security Considerations

### Code Execution Safety
- **Sandboxed execution**: Tool deserialization in controlled environment
- **Input validation**: All state inputs validated before persistence
- **Access controls**: Agent access restricted by user permissions
- **Audit logging**: All state changes logged for security review

### Data Protection
- **Encryption at rest**: Sensitive state data encrypted
- **Access logging**: All agent access logged
- **Data retention**: Configurable retention policies for state data
- **GDPR compliance**: Support for data deletion and export

## Testing Strategy

### Unit Tests
- **Tool serialization**: Round-trip serialization tests for various function types
- **State persistence**: Verify state save/load integrity
- **Agent lifecycle**: Test agent creation, modification, deletion
- **Error scenarios**: Test recovery from various failure modes

### Integration Tests
- **Canvas integration**: End-to-end tests with Canvas UI
- **Multi-agent workflows**: Test collaboration scenarios
- **Performance tests**: Load testing with many concurrent agents
- **Persistence tests**: Long-running agents with state evolution

### Example Test
```python
def test_persistent_tool_with_closure():
    """Test that tools with closures serialize correctly."""
    multiplier = 42
    
    def multiply_by_closure(x: int) -> int:
        return x * multiplier
    
    agent = PersistentA1("test_agent")
    agent.add_tool(multiply_by_closure)
    
    # Create new agent instance - should restore tool
    agent2 = PersistentA1("test_agent")
    
    # Test restored tool works
    restored_tool = agent2._custom_tools['multiply_by_closure']
    assert restored_tool(5) == 210  # 5 * 42
```

## Future Enhancements

### Phase 0.5: Advanced Features
- **State versioning**: Git-like versioning for agent state
- **Conflict resolution**: Merge strategies for concurrent state changes
- **State analytics**: Metrics on tool usage, data access patterns
- **Automated backup**: Scheduled backups of critical agent states

### Phase 1: Enterprise Features
- **Database backends**: PostgreSQL, Redis, MongoDB support
- **Distributed agents**: Agents spanning multiple compute nodes
- **State streaming**: Real-time state synchronization
- **Advanced monitoring**: Prometheus metrics, health checks

### Phase 2: Advanced Collaboration
- **Team workspaces**: Shared agent pools for research teams
- **Permission systems**: Fine-grained access controls
- **Workflow orchestration**: Complex multi-agent research pipelines
- **Integration APIs**: Connect with external research platforms

## Deployment Guide

### Development Setup
```bash
# Install dependencies
pip install -r requirements_state_foundation.txt

# Run tests
python -m pytest tests/test_state_foundation.py -v

# Run demo
python examples/state_foundation_demo.py
```

### Production Deployment
```yaml
# Docker Compose
version: '3.8'
services:
  biomni-state-foundation:
    build: .
    environment:
      - STATE_DIR=/data/agents
      - MAX_CONCURRENT_AGENTS=100
      - CLEANUP_INTERVAL_HOURS=24
    volumes:
      - agent_state_data:/data/agents
    ports:
      - "8001:8001"
```

### Configuration
```yaml
# config/state_foundation.yaml
state_management:
  base_dir: "/data/agents"
  auto_save: true
  max_concurrent_agents: 100
  cleanup_interval_hours: 24
  
serialization:
  primary_method: "dill"
  fallback_method: "source_code"
  compression: true
  
security:
  encrypt_state_files: true
  audit_logging: true
  sandbox_tool_execution: true
```

This State Management Foundation provides the critical infrastructure needed to transform biomni from a stateless framework into a persistent, collaborative research platform suitable for GenAI assistant integration.
