# Pre-Phase 0: State Management Foundation
# Implementation of PersistentA1 class with comprehensive state persistence

import json
import os
import sys
import subprocess
import sqlite3
import pickle
import base64
import dill
import inspect
from typing import Dict, Optional, Any, List, Callable, Union
from datetime import datetime
from pathlib import Path
import traceback
import logging

# Add biomni to Python path
biomni_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
if biomni_path not in sys.path:
    sys.path.insert(0, biomni_path)

from biomni.agent import A1

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ToolSerializationEngine:
    """Advanced tool serialization using dill for complex function persistence."""
    
    @staticmethod
    def serialize_function(func: Callable) -> Dict[str, Any]:
        """Serialize a function with comprehensive metadata."""
        try:
            # Try dill serialization first (most robust)
            serialized_bytes = dill.dumps(func)
            encoded_bytes = base64.b64encode(serialized_bytes).decode('utf-8')
            
            metadata = {
                'name': func.__name__,
                'doc': func.__doc__ or "",
                'module': getattr(func, '__module__', None),
                'qualname': getattr(func, '__qualname__', None),
                'annotations': getattr(func, '__annotations__', {}),
                'serialization_method': 'dill',
                'serialized_data': encoded_bytes,
                'timestamp': datetime.now().isoformat()
            }
            
            # Try to get source code as backup
            try:
                metadata['source_code'] = inspect.getsource(func)
            except (OSError, TypeError):
                metadata['source_code'] = None
                
            return metadata
            
        except Exception as e:
            logger.warning(f"Dill serialization failed for {func.__name__}: {e}")
            # Fallback to source code only
            return ToolSerializationEngine._fallback_serialization(func)
    
    @staticmethod
    def _fallback_serialization(func: Callable) -> Dict[str, Any]:
        """Fallback serialization using source code."""
        try:
            source_code = inspect.getsource(func)
            return {
                'name': func.__name__,
                'doc': func.__doc__ or "",
                'source_code': source_code,
                'serialization_method': 'source_code',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"All serialization methods failed for {func.__name__}: {e}")
            return {
                'name': func.__name__,
                'doc': func.__doc__ or "",
                'serialization_method': 'metadata_only',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    @staticmethod
    def deserialize_function(metadata: Dict[str, Any]) -> Optional[Callable]:
        """Deserialize a function from metadata."""
        try:
            if metadata.get('serialization_method') == 'dill':
                # Reconstruct from dill serialization
                encoded_bytes = metadata['serialized_data']
                serialized_bytes = base64.b64decode(encoded_bytes.encode('utf-8'))
                func = dill.loads(serialized_bytes)
                logger.info(f"Successfully deserialized function '{metadata['name']}' using dill")
                return func
                
            elif metadata.get('serialization_method') == 'source_code':
                # Reconstruct from source code
                source_code = metadata['source_code']
                if source_code:
                    exec_globals = {}
                    exec(source_code, exec_globals)
                    
                    # Find the function in executed globals
                    func_name = metadata['name']
                    if func_name in exec_globals and callable(exec_globals[func_name]):
                        func = exec_globals[func_name]
                        logger.info(f"Successfully deserialized function '{func_name}' from source code")
                        return func
                        
            logger.warning(f"Could not deserialize function '{metadata['name']}'")
            return None
            
        except Exception as e:
            logger.error(f"Error deserializing function '{metadata.get('name', 'unknown')}': {e}")
            return None


class PersistentA1(A1):
    """Extended A1 with comprehensive state persistence capabilities."""
    
    def __init__(self, agent_id: str = "default", state_dir: str = "./data/agent_states", **kwargs):
        """
        Initialize PersistentA1 with state persistence.
        
        Args:
            agent_id: Unique identifier for this agent instance
            state_dir: Directory to store agent state files
            **kwargs: Additional arguments passed to base A1 class
        """
        super().__init__(**kwargs)
        
        self.agent_id = agent_id
        self.state_dir = Path(state_dir)
        self.state_file = self.state_dir / f"{agent_id}.json"
        self.tools_dir = self.state_dir / "tools" / agent_id
        self.data_dir = self.state_dir / "data" / agent_id
        
        # Create directories
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize serialization engine
        self.serialization_engine = ToolSerializationEngine()
        
        # Track state changes for auto-save
        self._auto_save_enabled = kwargs.get('auto_save', True)
        self._state_dirty = False
        
        # Load existing state
        self._load_persistent_state()
        
        logger.info(f"Initialized PersistentA1 agent '{agent_id}' with state persistence")
    
    def _load_persistent_state(self):
        """Load agent state from persistent storage."""
        if not self.state_file.exists():
            logger.info(f"No existing state file for agent '{self.agent_id}', starting fresh")
            return
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            logger.info(f"Loading state for agent '{self.agent_id}' from {self.state_file}")
            
            # Restore custom tools
            if 'custom_tools' in state:
                self._restore_custom_tools(state['custom_tools'])
            
            # Restore custom data
            if 'custom_data' in state:
                self._restore_custom_data(state['custom_data'])
            
            # Restore custom software
            if 'custom_software' in state:
                self._restore_custom_software(state['custom_software'])
            
            # Restore agent configuration
            if 'agent_config' in state:
                self._restore_agent_config(state['agent_config'])
            
            logger.info(f"Successfully restored state for agent '{self.agent_id}'")
            
        except Exception as e:
            logger.error(f"Error loading state for agent '{self.agent_id}': {e}")
            logger.error(traceback.format_exc())
    
    def _restore_custom_tools(self, tools_data: Dict[str, Any]):
        """Restore custom tools from serialized data."""
        if not hasattr(self, '_custom_tools'):
            self._custom_tools = {}
        
        for tool_name, tool_metadata in tools_data.items():
            try:
                # Deserialize the function
                func = self.serialization_engine.deserialize_function(tool_metadata)
                if func:
                    # Add to custom tools without triggering save
                    self._custom_tools[tool_name] = func
                    
                    # Register with biomni tool registry
                    if hasattr(self, 'tool_registry'):
                        self.tool_registry.register_tool(func)
                    
                    logger.info(f"Restored custom tool: {tool_name}")
                else:
                    logger.warning(f"Failed to restore custom tool: {tool_name}")
                    
            except Exception as e:
                logger.error(f"Error restoring tool '{tool_name}': {e}")
    
    def _restore_custom_data(self, data_dict: Dict[str, str]):
        """Restore custom data references."""
        if not hasattr(self, '_custom_data'):
            self._custom_data = {}
        
        for data_key, description in data_dict.items():
            self._custom_data[data_key] = description
            logger.info(f"Restored custom data: {data_key}")
    
    def _restore_custom_software(self, software_dict: Dict[str, str]):
        """Restore custom software references."""
        if not hasattr(self, '_custom_software'):
            self._custom_software = {}
        
        for software_name, description in software_dict.items():
            self._custom_software[software_name] = description
            
            # Update library content dict if it exists
            if hasattr(self, 'library_content_dict'):
                self.library_content_dict[software_name] = description
            
            logger.info(f"Restored custom software: {software_name}")
    
    def _restore_agent_config(self, config: Dict[str, Any]):
        """Restore agent configuration."""
        # Store config for reference but don't override current instance
        self._original_config = config
        logger.info("Restored agent configuration")
    
    def _save_persistent_state(self):
        """Save current agent state to persistent storage."""
        if not self._auto_save_enabled:
            return
        
        try:
            state = {
                'agent_id': self.agent_id,
                'timestamp': datetime.now().isoformat(),
                'agent_config': {
                    'path': getattr(self, 'path', './data'),
                    'llm': getattr(self, 'llm', 'claude-3-5-sonnet-20241022'),
                    'use_tool_retriever': getattr(self, 'use_tool_retriever', True),
                    'timeout_seconds': getattr(self, 'timeout_seconds', 600)
                },
                'custom_tools': self._serialize_custom_tools(),
                'custom_data': dict(getattr(self, '_custom_data', {})),
                'custom_software': dict(getattr(self, '_custom_software', {})),
                'version': '1.0'
            }
            
            # Atomic write to prevent corruption
            temp_file = self.state_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            temp_file.replace(self.state_file)
            self._state_dirty = False
            
            logger.info(f"Saved state for agent '{self.agent_id}'")
            
        except Exception as e:
            logger.error(f"Error saving state for agent '{self.agent_id}': {e}")
            logger.error(traceback.format_exc())
    
    def _serialize_custom_tools(self) -> Dict[str, Any]:
        """Serialize all custom tools."""
        if not hasattr(self, '_custom_tools'):
            return {}
        
        serialized_tools = {}
        for tool_name, tool_func in self._custom_tools.items():
            try:
                serialized_tools[tool_name] = self.serialization_engine.serialize_function(tool_func)
            except Exception as e:
                logger.error(f"Error serializing tool '{tool_name}': {e}")
        
        return serialized_tools
    
    def add_tool(self, api: Callable) -> Any:
        """Override add_tool to add persistence."""
        result = super().add_tool(api)
        
        # Track custom tools for persistence
        if not hasattr(self, '_custom_tools'):
            self._custom_tools = {}
        
        self._custom_tools[api.__name__] = api
        self._state_dirty = True
        
        # Auto-save if enabled
        if self._auto_save_enabled:
            self._save_persistent_state()
        
        logger.info(f"Added and persisted custom tool: {api.__name__}")
        return result
    
    def add_data(self, data: Dict[str, str]) -> Any:
        """Override add_data to add persistence."""
        result = super().add_data(data)
        
        # Track custom data for persistence
        if not hasattr(self, '_custom_data'):
            self._custom_data = {}
        
        self._custom_data.update(data)
        self._state_dirty = True
        
        # Auto-save if enabled
        if self._auto_save_enabled:
            self._save_persistent_state()
        
        logger.info(f"Added and persisted custom data: {list(data.keys())}")
        return result
    
    def add_software(self, software: Dict[str, str], install: bool = False) -> Any:
        """Enhanced add_software with actual installation capability."""
        # Original behavior - add metadata
        result = super().add_software(software)
        
        # Track custom software for persistence
        if not hasattr(self, '_custom_software'):
            self._custom_software = {}
        
        for name, description in software.items():
            self._custom_software[name] = description
            
            # Optionally install actual packages
            if install:
                self._install_package(name)
        
        self._state_dirty = True
        
        # Auto-save if enabled
        if self._auto_save_enabled:
            self._save_persistent_state()
        
        logger.info(f"Added and persisted custom software: {list(software.keys())}")
        return result
    
    def _install_package(self, package_spec: str):
        """Install actual software packages."""
        try:
            if package_spec.startswith("pip:"):
                package = package_spec.replace("pip:", "")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", package],
                    check=True, capture_output=True, text=True
                )
                logger.info(f"Successfully installed pip package: {package}")
                
            elif package_spec.startswith("conda:"):
                package = package_spec.replace("conda:", "")
                result = subprocess.run(
                    ["conda", "install", "-y", package],
                    check=True, capture_output=True, text=True
                )
                logger.info(f"Successfully installed conda package: {package}")
                
            elif package_spec.startswith("r:"):
                package = package_spec.replace("r:", "")
                r_cmd = f'install.packages("{package}", repos="https://cran.r-project.org")'
                result = subprocess.run(
                    ["Rscript", "-e", r_cmd],
                    check=True, capture_output=True, text=True
                )
                logger.info(f"Successfully installed R package: {package}")
                
            else:
                # Try pip by default
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", package_spec],
                    check=True, capture_output=True, text=True
                )
                logger.info(f"Successfully installed package: {package_spec}")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install {package_spec}: {e}")
            logger.error(f"stderr: {e.stderr}")
        except Exception as e:
            logger.error(f"Error installing {package_spec}: {e}")
    
    def remove_custom_tool(self, tool_name: str):
        """Remove a custom tool from the agent."""
        if hasattr(self, '_custom_tools') and tool_name in self._custom_tools:
            del self._custom_tools[tool_name]
            self._state_dirty = True
            
            if self._auto_save_enabled:
                self._save_persistent_state()
            
            logger.info(f"Removed custom tool: {tool_name}")
        else:
            logger.warning(f"Tool '{tool_name}' not found in custom tools")
    
    def list_custom_tools(self) -> List[str]:
        """List all custom tool names."""
        if hasattr(self, '_custom_tools'):
            return list(self._custom_tools.keys())
        return []
    
    def get_custom_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get details about a custom tool."""
        if hasattr(self, '_custom_tools') and tool_name in self._custom_tools:
            func = self._custom_tools[tool_name]
            return {
                'name': func.__name__,
                'doc': func.__doc__,
                'module': getattr(func, '__module__', None),
                'annotations': getattr(func, '__annotations__', {})
            }
        return None
    
    def list_custom_data(self) -> List[str]:
        """List all custom data keys."""
        if hasattr(self, '_custom_data'):
            return list(self._custom_data.keys())
        return []
    
    def get_custom_data(self, data_key: str) -> Optional[str]:
        """Get description of custom data."""
        if hasattr(self, '_custom_data'):
            return self._custom_data.get(data_key)
        return None
    
    def remove_custom_data(self, data_key: str):
        """Remove custom data reference."""
        if hasattr(self, '_custom_data') and data_key in self._custom_data:
            del self._custom_data[data_key]
            self._state_dirty = True
            
            if self._auto_save_enabled:
                self._save_persistent_state()
            
            logger.info(f"Removed custom data: {data_key}")
    
    def save_state(self):
        """Manually save current state."""
        self._save_persistent_state()
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of current agent state."""
        return {
            'agent_id': self.agent_id,
            'custom_tools_count': len(getattr(self, '_custom_tools', {})),
            'custom_data_count': len(getattr(self, '_custom_data', {})),
            'custom_software_count': len(getattr(self, '_custom_software', {})),
            'state_file': str(self.state_file),
            'auto_save_enabled': self._auto_save_enabled,
            'state_dirty': self._state_dirty,
            'last_modified': datetime.fromtimestamp(self.state_file.stat().st_mtime).isoformat() if self.state_file.exists() else None
        }
    
    def export_state(self, export_path: str):
        """Export agent state to a specific file."""
        try:
            state = {
                'agent_id': self.agent_id,
                'timestamp': datetime.now().isoformat(),
                'custom_tools': self._serialize_custom_tools(),
                'custom_data': dict(getattr(self, '_custom_data', {})),
                'custom_software': dict(getattr(self, '_custom_software', {})),
                'export_version': '1.0'
            }
            
            with open(export_path, 'w') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported agent state to {export_path}")
            
        except Exception as e:
            logger.error(f"Error exporting state: {e}")
            raise
    
    def import_state(self, import_path: str, merge: bool = True):
        """Import agent state from a file."""
        try:
            with open(import_path, 'r') as f:
                state = json.load(f)
            
            if not merge:
                # Clear existing state
                self._custom_tools = {}
                self._custom_data = {}
                self._custom_software = {}
            
            # Import tools
            if 'custom_tools' in state:
                self._restore_custom_tools(state['custom_tools'])
            
            # Import data
            if 'custom_data' in state:
                if merge and hasattr(self, '_custom_data'):
                    self._custom_data.update(state['custom_data'])
                else:
                    self._custom_data = state['custom_data']
            
            # Import software
            if 'custom_software' in state:
                if merge and hasattr(self, '_custom_software'):
                    self._custom_software.update(state['custom_software'])
                else:
                    self._custom_software = state['custom_software']
            
            # Save the updated state
            self._save_persistent_state()
            
            logger.info(f"Imported agent state from {import_path}")
            
        except Exception as e:
            logger.error(f"Error importing state: {e}")
            raise


class GlobalAgentManager:
    """Singleton service for managing persistent agent instances across sessions."""
    
    _instance = None
    _agents: Dict[str, PersistentA1] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, base_state_dir: str = "./data/agents"):
        if self._initialized:
            return
        
        self.base_state_dir = Path(base_state_dir)
        self.base_state_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = True
        
        logger.info(f"Initialized GlobalAgentManager with base directory: {base_state_dir}")
    
    def create_agent(
        self, 
        agent_id: str, 
        overwrite: bool = False,
        **agent_kwargs
    ) -> PersistentA1:
        """Create a new persistent agent."""
        if agent_id in self._agents and not overwrite:
            logger.warning(f"Agent '{agent_id}' already exists, returning existing instance")
            return self._agents[agent_id]
        
        # Set up state directory for this agent
        agent_state_dir = self.base_state_dir / "states"
        agent_kwargs['state_dir'] = str(agent_state_dir)
        
        # Create the agent
        agent = PersistentA1(agent_id=agent_id, **agent_kwargs)
        self._agents[agent_id] = agent
        
        logger.info(f"Created persistent agent: {agent_id}")
        return agent
    
    def get_agent(self, agent_id: str, **agent_kwargs) -> PersistentA1:
        """Get existing agent or create new one."""
        if agent_id in self._agents:
            return self._agents[agent_id]
        
        return self.create_agent(agent_id, **agent_kwargs)
    
    def list_agents(self) -> List[str]:
        """List all agent IDs."""
        # Include both in-memory agents and agents with state files
        in_memory = set(self._agents.keys())
        
        state_dir = self.base_state_dir / "states"
        on_disk = set()
        if state_dir.exists():
            for state_file in state_dir.glob("*.json"):
                agent_id = state_file.stem
                on_disk.add(agent_id)
        
        return sorted(in_memory.union(on_disk))
    
    def delete_agent(self, agent_id: str, remove_files: bool = True):
        """Delete an agent and optionally its persistent state."""
        # Remove from memory
        if agent_id in self._agents:
            del self._agents[agent_id]
        
        # Remove state files if requested
        if remove_files:
            state_dir = self.base_state_dir / "states"
            state_file = state_dir / f"{agent_id}.json"
            if state_file.exists():
                state_file.unlink()
            
            # Remove agent-specific directories
            tools_dir = state_dir / "tools" / agent_id
            data_dir = state_dir / "data" / agent_id
            
            if tools_dir.exists():
                import shutil
                shutil.rmtree(tools_dir)
            
            if data_dir.exists():
                import shutil
                shutil.rmtree(data_dir)
        
        logger.info(f"Deleted agent: {agent_id}")
    
    def clone_agent(self, source_agent_id: str, target_agent_id: str) -> PersistentA1:
        """Clone an existing agent to a new agent ID."""
        if source_agent_id not in self._agents:
            # Try to load the source agent
            source_agent = self.get_agent(source_agent_id)
        else:
            source_agent = self._agents[source_agent_id]
        
        # Export source agent state
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            source_agent.export_state(temp_file.name)
            temp_path = temp_file.name
        
        try:
            # Create new agent
            target_agent = self.create_agent(target_agent_id)
            
            # Import state from source
            target_agent.import_state(temp_path, merge=False)
            
            logger.info(f"Cloned agent from '{source_agent_id}' to '{target_agent_id}'")
            return target_agent
            
        finally:
            # Clean up temp file
            os.unlink(temp_path)
    
    def get_agent_summary(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get summary information about an agent."""
        if agent_id in self._agents:
            return self._agents[agent_id].get_state_summary()
        
        # Try to get info from state file
        state_dir = self.base_state_dir / "states"
        state_file = state_dir / f"{agent_id}.json"
        
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                return {
                    'agent_id': agent_id,
                    'in_memory': False,
                    'last_modified': datetime.fromtimestamp(state_file.stat().st_mtime).isoformat(),
                    'custom_tools_count': len(state.get('custom_tools', {})),
                    'custom_data_count': len(state.get('custom_data', {})),
                    'custom_software_count': len(state.get('custom_software', {}))
                }
            except Exception as e:
                logger.error(f"Error reading state file for agent '{agent_id}': {e}")
        
        return None
    
    def cleanup_unused_agents(self, max_idle_hours: int = 24):
        """Remove agents that haven't been used recently."""
        cutoff_time = datetime.now().timestamp() - (max_idle_hours * 3600)
        
        to_remove = []
        for agent_id, agent in self._agents.items():
            if agent.state_file.exists():
                last_modified = agent.state_file.stat().st_mtime
                if last_modified < cutoff_time:
                    to_remove.append(agent_id)
        
        for agent_id in to_remove:
            del self._agents[agent_id]
            logger.info(f"Cleaned up unused agent: {agent_id}")
        
        return len(to_remove)


# Global instance
agent_manager = GlobalAgentManager()
