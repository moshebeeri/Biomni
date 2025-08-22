#!/usr/bin/env python3
"""
Test suite for Pre-Phase 0: State Management Foundation
Tests PersistentA1, GlobalAgentManager, and ToolSerializationEngine
"""

import pytest
import tempfile
import json
import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add the app directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from biomni.persistent_agent import (
    PersistentA1, 
    GlobalAgentManager, 
    ToolSerializationEngine,
    agent_manager
)


class TestToolSerializationEngine:
    """Test tool serialization and deserialization."""
    
    def test_serialize_simple_function(self):
        """Test serialization of a simple function."""
        def simple_function(x: int, y: int = 5) -> int:
            """Add two numbers."""
            return x + y
        
        engine = ToolSerializationEngine()
        metadata = engine.serialize_function(simple_function)
        
        assert metadata['name'] == 'simple_function'
        assert metadata['doc'] == 'Add two numbers.'
        assert 'serialized_data' in metadata or 'source_code' in metadata
        assert metadata['serialization_method'] in ['dill', 'source_code']
    
    def test_deserialize_simple_function(self):
        """Test deserialization of a simple function."""
        def simple_function(x: int, y: int = 5) -> int:
            """Add two numbers."""
            return x + y
        
        engine = ToolSerializationEngine()
        metadata = engine.serialize_function(simple_function)
        restored_func = engine.deserialize_function(metadata)
        
        assert restored_func is not None
        assert restored_func.__name__ == 'simple_function'
        assert restored_func(3, 4) == 7
        assert restored_func(10) == 15  # Test default parameter
    
    def test_serialize_complex_function_with_closure(self):
        """Test serialization of function with closure."""
        multiplier = 10
        
        def complex_function(x: int) -> int:
            """Multiply by closure variable."""
            return x * multiplier
        
        engine = ToolSerializationEngine()
        metadata = engine.serialize_function(complex_function)
        
        assert metadata['name'] == 'complex_function'
        # Should use dill for closure functions
        if metadata['serialization_method'] == 'dill':
            restored_func = engine.deserialize_function(metadata)
            assert restored_func is not None
            assert restored_func(5) == 50
    
    def test_fallback_serialization(self):
        """Test fallback when serialization fails."""
        # Mock a function that can't be serialized with dill
        mock_func = MagicMock()
        mock_func.__name__ = 'mock_func'
        mock_func.__doc__ = 'Mock function'
        
        engine = ToolSerializationEngine()
        
        # Should fall back to metadata-only
        with patch('dill.dumps', side_effect=Exception("Serialization failed")):
            with patch('inspect.getsource', side_effect=OSError("No source")):
                metadata = engine._fallback_serialization(mock_func)
                
                assert metadata['name'] == 'mock_func'
                assert metadata['serialization_method'] == 'metadata_only'
                assert 'error' in metadata


class TestPersistentA1:
    """Test PersistentA1 agent with state persistence."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_a1_base(self):
        """Mock the base A1 class."""
        with patch('biomni.persistent_agent.A1') as mock_a1:
            mock_instance = MagicMock()
            mock_a1.return_value = mock_instance
            yield mock_instance
    
    def test_persistent_a1_initialization(self, temp_dir, mock_a1_base):
        """Test PersistentA1 initialization."""
        agent = PersistentA1(
            agent_id="test_agent",
            state_dir=temp_dir,
            path="./data",
            auto_save=True
        )
        
        assert agent.agent_id == "test_agent"
        assert agent.state_dir == Path(temp_dir)
        assert agent._auto_save_enabled is True
        
        # Check directories were created
        assert agent.tools_dir.exists()
        assert agent.data_dir.exists()
    
    def test_add_tool_with_persistence(self, temp_dir, mock_a1_base):
        """Test adding tools with automatic persistence."""
        agent = PersistentA1(agent_id="test_agent", state_dir=temp_dir)
        
        def test_tool(x: int) -> int:
            """Test tool function."""
            return x * 2
        
        # Mock the parent add_tool method
        mock_a1_base.add_tool.return_value = "success"
        
        result = agent.add_tool(test_tool)
        
        # Verify tool was added to custom tools
        assert 'test_tool' in agent._custom_tools
        assert agent._custom_tools['test_tool'] == test_tool
        
        # Verify state file was created
        assert agent.state_file.exists()
        
        # Verify state file contains the tool
        with open(agent.state_file, 'r') as f:
            state = json.load(f)
        
        assert 'custom_tools' in state
        assert 'test_tool' in state['custom_tools']
    
    def test_add_data_with_persistence(self, temp_dir, mock_a1_base):
        """Test adding data with automatic persistence."""
        agent = PersistentA1(agent_id="test_agent", state_dir=temp_dir)
        
        test_data = {
            "dataset1.csv": "Test dataset description",
            "experiment_results.json": "Experiment results data"
        }
        
        mock_a1_base.add_data.return_value = "success"
        
        result = agent.add_data(test_data)
        
        # Verify data was added
        assert hasattr(agent, '_custom_data')
        assert agent._custom_data['dataset1.csv'] == "Test dataset description"
        assert agent._custom_data['experiment_results.json'] == "Experiment results data"
        
        # Verify persistence
        with open(agent.state_file, 'r') as f:
            state = json.load(f)
        
        assert state['custom_data'] == test_data
    
    def test_enhanced_add_software(self, temp_dir, mock_a1_base):
        """Test enhanced add_software with installation."""
        agent = PersistentA1(agent_id="test_agent", state_dir=temp_dir)
        
        test_software = {
            "numpy": "Numerical computing library",
            "pip:requests": "HTTP library"
        }
        
        mock_a1_base.add_software.return_value = "success"
        
        # Test without installation
        with patch.object(agent, '_install_package') as mock_install:
            agent.add_software(test_software, install=False)
            mock_install.assert_not_called()
        
        # Test with installation
        with patch.object(agent, '_install_package') as mock_install:
            agent.add_software(test_software, install=True)
            mock_install.assert_called()
    
    def test_state_restoration(self, temp_dir, mock_a1_base):
        """Test state restoration from saved file."""
        # Create initial agent and add some state
        agent1 = PersistentA1(agent_id="test_agent", state_dir=temp_dir)
        
        def test_function(x: int) -> str:
            """Convert int to string."""
            return str(x)
        
        mock_a1_base.add_tool.return_value = "success"
        mock_a1_base.add_data.return_value = "success"
        
        agent1.add_tool(test_function)
        agent1.add_data({"test.csv": "Test data"})
        
        # Create new agent with same ID - should restore state
        agent2 = PersistentA1(agent_id="test_agent", state_dir=temp_dir)
        
        # Verify state was restored
        assert hasattr(agent2, '_custom_tools')
        assert hasattr(agent2, '_custom_data')
        assert 'test.csv' in agent2._custom_data
    
    def test_tool_management_methods(self, temp_dir, mock_a1_base):
        """Test tool management methods."""
        agent = PersistentA1(agent_id="test_agent", state_dir=temp_dir)
        
        def tool1(x: int) -> int:
            return x + 1
        
        def tool2(x: str) -> str:
            return x.upper()
        
        mock_a1_base.add_tool.return_value = "success"
        
        # Add tools
        agent.add_tool(tool1)
        agent.add_tool(tool2)
        
        # Test list_custom_tools
        tools = agent.list_custom_tools()
        assert 'tool1' in tools
        assert 'tool2' in tools
        
        # Test get_custom_tool
        tool_info = agent.get_custom_tool('tool1')
        assert tool_info['name'] == 'tool1'
        
        # Test remove_custom_tool
        agent.remove_custom_tool('tool1')
        assert 'tool1' not in agent.list_custom_tools()
        assert 'tool2' in agent.list_custom_tools()
    
    def test_export_import_state(self, temp_dir, mock_a1_base):
        """Test state export and import."""
        agent1 = PersistentA1(agent_id="agent1", state_dir=temp_dir)
        
        def test_tool() -> str:
            return "test"
        
        mock_a1_base.add_tool.return_value = "success"
        mock_a1_base.add_data.return_value = "success"
        
        agent1.add_tool(test_tool)
        agent1.add_data({"data.csv": "Test data"})
        
        # Export state
        export_path = os.path.join(temp_dir, "exported_state.json")
        agent1.export_state(export_path)
        
        assert os.path.exists(export_path)
        
        # Create new agent and import state
        agent2 = PersistentA1(agent_id="agent2", state_dir=temp_dir)
        agent2.import_state(export_path, merge=False)
        
        # Verify import
        assert 'test_tool' in agent2._custom_tools
        assert 'data.csv' in agent2._custom_data


class TestGlobalAgentManager:
    """Test GlobalAgentManager singleton service."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def clean_manager(self, temp_dir):
        """Create clean manager instance for testing."""
        # Reset the singleton
        GlobalAgentManager._instance = None
        GlobalAgentManager._agents = {}
        
        manager = GlobalAgentManager(base_state_dir=temp_dir)
        yield manager
        
        # Cleanup
        GlobalAgentManager._instance = None
        GlobalAgentManager._agents = {}
    
    def test_singleton_behavior(self, temp_dir):
        """Test that GlobalAgentManager is a singleton."""
        manager1 = GlobalAgentManager(base_state_dir=temp_dir)
        manager2 = GlobalAgentManager(base_state_dir="different_path")
        
        assert manager1 is manager2
    
    def test_create_agent(self, clean_manager, temp_dir):
        """Test agent creation."""
        with patch('biomni.persistent_agent.PersistentA1') as mock_persistent_a1:
            mock_agent = MagicMock()
            mock_persistent_a1.return_value = mock_agent
            
            agent = clean_manager.create_agent("test_agent")
            
            assert "test_agent" in clean_manager._agents
            assert clean_manager._agents["test_agent"] == mock_agent
            mock_persistent_a1.assert_called_once()
    
    def test_get_agent(self, clean_manager, temp_dir):
        """Test getting existing or creating new agent."""
        with patch('biomni.persistent_agent.PersistentA1') as mock_persistent_a1:
            mock_agent = MagicMock()
            mock_persistent_a1.return_value = mock_agent
            
            # First call should create agent
            agent1 = clean_manager.get_agent("test_agent")
            
            # Second call should return existing agent
            agent2 = clean_manager.get_agent("test_agent")
            
            assert agent1 == agent2
            assert mock_persistent_a1.call_count == 1
    
    def test_list_agents(self, clean_manager, temp_dir):
        """Test listing agents."""
        with patch('biomni.persistent_agent.PersistentA1') as mock_persistent_a1:
            mock_persistent_a1.return_value = MagicMock()
            
            # Create some agents
            clean_manager.create_agent("agent1")
            clean_manager.create_agent("agent2")
            
            agents = clean_manager.list_agents()
            assert "agent1" in agents
            assert "agent2" in agents
    
    def test_delete_agent(self, clean_manager, temp_dir):
        """Test agent deletion."""
        with patch('biomni.persistent_agent.PersistentA1') as mock_persistent_a1:
            mock_agent = MagicMock()
            mock_agent.state_file = Path(temp_dir) / "states" / "test_agent.json"
            mock_persistent_a1.return_value = mock_agent
            
            # Create agent
            clean_manager.create_agent("test_agent")
            assert "test_agent" in clean_manager._agents
            
            # Delete agent
            clean_manager.delete_agent("test_agent", remove_files=False)
            assert "test_agent" not in clean_manager._agents
    
    def test_clone_agent(self, clean_manager, temp_dir):
        """Test agent cloning."""
        with patch('biomni.persistent_agent.PersistentA1') as mock_persistent_a1:
            # Mock source agent
            source_agent = MagicMock()
            source_agent.export_state = MagicMock()
            
            # Mock target agent  
            target_agent = MagicMock()
            target_agent.import_state = MagicMock()
            
            # Set up mock to return different agents
            mock_persistent_a1.side_effect = [source_agent, target_agent]
            
            # Add source agent to manager
            clean_manager._agents["source_agent"] = source_agent
            
            # Clone agent
            with patch('tempfile.NamedTemporaryFile') as mock_temp:
                mock_temp.return_value.__enter__.return_value.name = "/tmp/test.json"
                mock_temp.return_value.__exit__.return_value = None
                
                with patch('os.unlink'):
                    cloned = clean_manager.clone_agent("source_agent", "target_agent")
                
                # Verify cloning process
                source_agent.export_state.assert_called_once()
                target_agent.import_state.assert_called_once()
                assert "target_agent" in clean_manager._agents


def test_integration_persistent_agent_with_manager(temp_dir=None):
    """Integration test: PersistentA1 with GlobalAgentManager."""
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp()
    
    try:
        # Reset manager
        GlobalAgentManager._instance = None
        GlobalAgentManager._agents = {}
        
        manager = GlobalAgentManager(base_state_dir=temp_dir)
        
        with patch('biomni.persistent_agent.A1') as mock_a1:
            mock_instance = MagicMock()
            mock_a1.return_value = mock_instance
            mock_instance.add_tool.return_value = "success"
            
            # Create agent through manager
            agent = manager.get_agent("integration_test")
            
            # Add a tool
            def integration_tool(x: int) -> int:
                """Integration test tool."""
                return x * 3
            
            agent.add_tool(integration_tool)
            
            # Verify tool was added and persisted
            assert 'integration_tool' in agent._custom_tools
            assert agent.state_file.exists()
            
            # Create another agent instance with same ID
            agent2 = manager.get_agent("integration_test")
            
            # Should be the same instance (in-memory)
            assert agent is agent2
            
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
