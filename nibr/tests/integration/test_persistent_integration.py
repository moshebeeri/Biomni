#!/usr/bin/env python3
"""
Test script to verify PersistentA1 and GlobalAgentManager integration
"""

import sys
import os
import json

# Add path to nibr/src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_persistent_a1():
    """Test PersistentA1 basic functionality."""
    print("Testing PersistentA1...")
    
    try:
        from persistent_a1 import PersistentA1
        
        # Create test agent
        agent = PersistentA1(
            path="./test_data",
            agent_id="test_agent_001"
        )
        
        # Add test data
        agent.add_data({"test_file.csv": "Test dataset for validation"})
        
        # Define and add a custom tool
        def analyze_test_data(data: str) -> str:
            """Custom test analysis tool."""
            return f"Analyzed: {data}"
        
        agent.add_tool(analyze_test_data)
        
        # Get state summary
        summary = agent.get_state_summary()
        print(f"✓ PersistentA1 created with agent_id: {summary['agent_id']}")
        print(f"  - Tools count: {summary['tools_count']}")
        print(f"  - Data count: {summary['data_count']}")
        print(f"  - State file: {summary['state_file']}")
        
        return True
        
    except Exception as e:
        print(f"✗ PersistentA1 test failed: {e}")
        return False

def test_global_agent_manager():
    """Test GlobalAgentManager functionality."""
    print("\nTesting GlobalAgentManager...")
    
    try:
        from global_agent_manager import agent_manager
        
        # Get or create an agent
        agent1 = agent_manager.get_agent("researcher_001")
        
        # Add some data
        agent1.add_data({"experiment_data.csv": "Protein interaction data"})
        
        # List all agents
        agents = agent_manager.list_agents()
        print(f"✓ GlobalAgentManager working")
        print(f"  - Total agents: {len(agents)}")
        print(f"  - Agent IDs: {agents}")
        
        # Get statistics
        stats = agent_manager.get_statistics()
        print(f"  - Loaded agents: {stats['loaded_agents']}")
        print(f"  - Base path: {stats['base_path']}")
        
        # Test cloning
        cloned = agent_manager.clone_agent("researcher_001", "researcher_002")
        if cloned:
            print(f"✓ Successfully cloned agent")
        
        return True
        
    except Exception as e:
        print(f"✗ GlobalAgentManager test failed: {e}")
        return False

def test_canvas_integration():
    """Test Canvas biomni_wrapper integration."""
    print("\nTesting Canvas Integration...")
    
    try:
        # Change to canvas scripts directory
        canvas_scripts = os.path.join(os.path.dirname(__file__), 'canvas/scripts')
        sys.path.insert(0, canvas_scripts)
        
        # Try importing the wrapper
        from biomni_wrapper import BiomniWrapper
        
        # Create test wrapper instance
        wrapper = BiomniWrapper("test_canvas_agent", "test_user")
        
        # Check agent type
        agent_type = type(wrapper.agent).__name__
        print(f"✓ Canvas wrapper initialized")
        print(f"  - Agent type: {agent_type}")
        print(f"  - Agent ID: {wrapper.agent_id}")
        
        # Check if it's using PersistentA1
        from persistent_a1 import PersistentA1
        if isinstance(wrapper.agent, PersistentA1):
            print(f"✓ Canvas is using PersistentA1 for state persistence")
            state_summary = wrapper.agent.get_state_summary()
            print(f"  - State file: {state_summary['state_file']}")
            print(f"  - State exists: {state_summary['state_exists']}")
        else:
            print(f"⚠ Canvas is using {agent_type} (not PersistentA1)")
        
        return True
        
    except ImportError as e:
        print(f"⚠ Canvas integration not fully available: {e}")
        print("  This is expected if biomni is not installed")
        return False
    except Exception as e:
        print(f"✗ Canvas integration test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing PersistentA1 and GlobalAgentManager Integration")
    print("=" * 60)
    
    results = []
    
    # Test each component
    results.append(("PersistentA1", test_persistent_a1()))
    results.append(("GlobalAgentManager", test_global_agent_manager()))
    results.append(("Canvas Integration", test_canvas_integration()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name:.<40} {status}")
    
    # Overall result
    all_passed = all(r[1] for r in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed - check output above")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())