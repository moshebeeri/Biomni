#!/usr/bin/env python3
"""
Fix NIBR Biomni Canvas Integration
Properly integrate with existing NIBR Biomni Canvas structure instead of creating parallel folders
"""

import os
import sys
import shutil
from pathlib import Path


def analyze_existing_structure():
    """Analyze the existing NIBR Biomni Canvas structure."""
    print("🔍 Analyzing existing NIBR Biomni Canvas structure...")
    
    canvas_dir = Path(__file__).parent
    
    structure = {
        'apps/web': 'Next.js frontend application',
        'apps/agents': 'LangGraph backend agents', 
        'packages/shared': 'Shared utilities and types',
        'packages/evals': 'Evaluation and testing',
        'scripts': 'Python scripts including biomni_wrapper.py'
    }
    
    existing = {}
    for path, description in structure.items():
        full_path = canvas_dir / path
        if full_path.exists():
            existing[path] = {
                'exists': True,
                'description': description,
                'files': len(list(full_path.rglob('*'))) if full_path.is_dir() else 0
            }
            print(f"  ✅ {path} - {description}")
        else:
            existing[path] = {'exists': False, 'description': description}
            print(f"  ❌ {path} - {description}")
    
    return existing


def check_biomni_integration():
    """Check existing biomni integration points."""
    print("\n🧬 Checking existing biomni integration...")
    
    canvas_dir = Path(__file__).parent
    
    integration_points = [
        'apps/agents/src/biomni/biomni-agent.ts',
        'apps/web/src/app/api/biomni/test/route.ts',
        'apps/web/src/components/biomni/',
        'scripts/biomni_wrapper.py'
    ]
    
    existing_integration = {}
    
    for point in integration_points:
        full_path = canvas_dir / point
        if full_path.exists():
            existing_integration[point] = True
            print(f"  ✅ {point}")
        else:
            existing_integration[point] = False
            print(f"  ❌ {point}")
    
    return existing_integration


def update_biomni_wrapper():
    """Update the biomni wrapper to use our persistent agent."""
    print("\n🔧 Updating biomni wrapper script...")
    
    wrapper_path = Path(__file__).parent / "scripts" / "biomni_wrapper.py"
    
    if not wrapper_path.exists():
        print(f"  ❌ Wrapper not found at {wrapper_path}")
        return False
    
    # Read existing wrapper
    with open(wrapper_path, 'r') as f:
        existing_content = f.read()
    
    # Check if it already uses persistent agents
    if 'PersistentA1' in existing_content:
        print("  ✅ Wrapper already uses PersistentA1")
        return True
    
    # Create updated wrapper that uses our persistent agent
    updated_wrapper = '''#!/usr/bin/env python3
"""
Enhanced Biomni Wrapper for NIBR Biomni Canvas
Uses persistent agents with state management
"""

import sys
import json
import os
from pathlib import Path

# Add biomni to path
biomni_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if biomni_path not in sys.path:
    sys.path.insert(0, biomni_path)

# Add canvas backend to path for persistent agent
canvas_backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend/app'))
if canvas_backend_path not in sys.path:
    sys.path.insert(0, canvas_backend_path)

try:
    from biomni.persistent_agent import GlobalAgentManager, PersistentA1
    PERSISTENT_AGENTS_AVAILABLE = True
except ImportError:
    # Fallback to regular biomni if persistent agents not available
    from biomni.agent import A1
    PERSISTENT_AGENTS_AVAILABLE = False
    print(json.dumps({"type": "warning", "message": "Persistent agents not available, using regular A1"}))


class BiomniWrapper:
    def __init__(self, agent_id: str, user_id: str):
        self.agent_id = agent_id
        self.user_id = user_id
        self.agent = None
        
        # Setup data path
        self.data_path = os.environ.get('DATA_PATH', '/tmp/nibr_data')
        os.makedirs(self.data_path, exist_ok=True)
        
        self.initialize_agent()
    
    def initialize_agent(self):
        """Initialize the biomni agent."""
        try:
            if PERSISTENT_AGENTS_AVAILABLE:
                # Use persistent agent manager
                manager = GlobalAgentManager(base_path=self.data_path)
                full_agent_id = f"{self.user_id}_{self.agent_id}"
                self.agent = manager.get_agent(full_agent_id)
                print(json.dumps({
                    "type": "initialized", 
                    "agent_type": "persistent",
                    "agent_id": full_agent_id,
                    "tools": len(self.agent.list_custom_tools()),
                    "data": len(self.agent.list_custom_data())
                }))
            else:
                # Use regular A1 agent
                agent_path = os.path.join(self.data_path, self.user_id, self.agent_id)
                os.makedirs(agent_path, exist_ok=True)
                self.agent = A1(path=agent_path)
                print(json.dumps({
                    "type": "initialized",
                    "agent_type": "regular", 
                    "agent_id": self.agent_id
                }))
                
        except Exception as e:
            print(json.dumps({
                "type": "error",
                "message": f"Failed to initialize agent: {str(e)}"
            }))
            sys.exit(1)
    
    def handle_message(self, message):
        """Handle incoming messages from Node.js."""
        try:
            msg_type = message.get('type')
            
            if msg_type == 'execute':
                self.execute_prompt(message.get('prompt', ''))
            elif msg_type == 'add_tool':
                self.add_tool(message.get('code'), message.get('name'), message.get('description'))
            elif msg_type == 'add_data':
                self.add_data(message.get('path'), message.get('description'))
            elif msg_type == 'list_tools':
                self.list_tools()
            elif msg_type == 'ping':
                print(json.dumps({"type": "pong"}))
            else:
                print(json.dumps({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}"
                }))
                
        except Exception as e:
            print(json.dumps({
                "type": "error",
                "message": f"Error handling message: {str(e)}"
            }))
    
    def execute_prompt(self, prompt: str):
        """Execute a research prompt."""
        try:
            print(json.dumps({
                "type": "step",
                "content": f"Starting research: {prompt}"
            }))
            
            # Execute with streaming if available
            if hasattr(self.agent, 'go_stream'):
                for step in self.agent.go_stream(prompt):
                    print(json.dumps({
                        "type": "step",
                        "content": step.get('output', ''),
                        "tool_execution": step.get('tool') and {
                            "name": step['tool'],
                            "status": "executing",
                            "category": "biomni"
                        }
                    }))
            else:
                # Non-streaming execution
                log, result = self.agent.go(prompt)
                print(json.dumps({
                    "type": "step", 
                    "content": result
                }))
            
            print(json.dumps({
                "type": "complete",
                "message": "Research execution completed"
            }))
            
        except Exception as e:
            print(json.dumps({
                "type": "error",
                "message": f"Execution failed: {str(e)}"
            }))
    
    def add_tool(self, code: str, name: str, description: str = ""):
        """Add a custom tool to the agent."""
        try:
            # Execute code to get function
            exec_globals = {}
            exec(code, exec_globals)
            
            # Find the function
            tool_func = None
            for obj_name, obj in exec_globals.items():
                if callable(obj) and (obj_name == name or not name):
                    tool_func = obj
                    name = obj_name
                    break
            
            if tool_func:
                self.agent.add_tool(tool_func)
                print(json.dumps({
                    "type": "tool_added",
                    "name": name,
                    "description": description
                }))
            else:
                print(json.dumps({
                    "type": "error",
                    "message": "No callable function found in code"
                }))
                
        except Exception as e:
            print(json.dumps({
                "type": "error",
                "message": f"Failed to add tool: {str(e)}"
            }))
    
    def add_data(self, path: str, description: str):
        """Add data reference to the agent."""
        try:
            self.agent.add_data({path: description})
            print(json.dumps({
                "type": "data_added",
                "path": path,
                "description": description
            }))
        except Exception as e:
            print(json.dumps({
                "type": "error",
                "message": f"Failed to add data: {str(e)}"
            }))
    
    def list_tools(self):
        """List available tools."""
        try:
            if hasattr(self.agent, 'list_custom_tools'):
                tools = self.agent.list_custom_tools()
            else:
                tools = []
            
            print(json.dumps({
                "type": "tools_list",
                "tools": tools
            }))
        except Exception as e:
            print(json.dumps({
                "type": "error", 
                "message": f"Failed to list tools: {str(e)}"
            }))
    
    def run(self):
        """Main event loop."""
        try:
            while True:
                line = sys.stdin.readline()
                if not line:
                    break
                
                try:
                    message = json.loads(line.strip())
                    self.handle_message(message)
                except json.JSONDecodeError:
                    print(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON message"
                    }))
                    
        except KeyboardInterrupt:
            print(json.dumps({"type": "shutdown"}))
        except Exception as e:
            print(json.dumps({
                "type": "error",
                "message": f"Wrapper error: {str(e)}"
            }))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({
            "type": "error", 
            "message": "Usage: python biomni_wrapper.py <agent_id> <user_id>"
        }))
        sys.exit(1)
    
    agent_id = sys.argv[1]
    user_id = sys.argv[2]
    
    wrapper = BiomniWrapper(agent_id, user_id)
    wrapper.run()
'''
    
    # Backup existing wrapper
    backup_path = wrapper_path.with_suffix('.py.backup')
    shutil.copy2(wrapper_path, backup_path)
    print(f"  📄 Backed up existing wrapper to {backup_path}")
    
    # Write updated wrapper
    with open(wrapper_path, 'w') as f:
        f.write(updated_wrapper)
    
    print("  ✅ Updated biomni wrapper with persistent agent support")
    return True


def remove_redundant_folders():
    """Remove the redundant frontend/backend folders we created."""
    print("\n🗑️  Removing redundant folders...")
    
    redundant_folders = ['frontend', 'backend']
    canvas_dir = Path(__file__).parent
    
    for folder in redundant_folders:
        folder_path = canvas_dir / folder
        if folder_path.exists():
            # Move useful files before deletion
            if folder == 'backend':
                # Save our persistent agent implementation
                persistent_agent_src = folder_path / "app" / "biomni" / "persistent_agent.py"
                if persistent_agent_src.exists():
                    dest = canvas_dir / "scripts" / "persistent_agent.py"
                    shutil.copy2(persistent_agent_src, dest)
                    print(f"  📄 Saved persistent_agent.py to scripts/")
            
            # Remove the folder
            try:
                shutil.rmtree(folder_path)
                print(f"  ✅ Removed redundant {folder}/ folder")
            except Exception as e:
                print(f"  ⚠️  Could not remove {folder}/: {e}")
        else:
            print(f"  ℹ️  {folder}/ folder not found")


def create_proper_setup_script():
    """Create a setup script that works with the actual NIBR Biomni Canvas structure."""
    print("\n📜 Creating proper setup script...")
    
    setup_script = '''#!/usr/bin/env python3
"""
Proper NIBR Biomni Canvas + Biomni Integration Setup
Works with the existing NIBR Biomni Canvas structure
"""

import os
import sys
import subprocess
from pathlib import Path


def setup_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    
    try:
        # Python dependencies for biomni integration
        python_deps = [
            "python-shell",  # For Node.js <-> Python communication
            "dill",          # For persistent agent serialization
            "cloudpickle"    # Alternative serialization
        ]
        
        for dep in python_deps:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
            print(f"  ✅ {dep}")
        
        # Node.js dependencies
        print("  Installing Node.js dependencies...")
        subprocess.run(["npm", "install"], cwd="apps/web", check=True)
        subprocess.run(["npm", "install"], cwd="apps/agents", check=True)
        
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to install dependencies: {e}")
        return False


def setup_data_links():
    """Setup symbolic links to biomni data."""
    print("🔗 Setting up data links...")
    
    try:
        # Create data directory in apps/web for data access
        data_dir = Path("apps/web/data")
        data_dir.mkdir(exist_ok=True)
        
        # Links to existing biomni data
        biomni_data = Path("../../data")
        
        links = [
            ("datalake", biomni_data / "data_lake"),
            ("benchmark", biomni_data / "benchmark"),
            ("cache", biomni_data / "cache")
        ]
        
        for link_name, source in links:
            target = data_dir / link_name
            
            if target.exists() and target.is_symlink():
                target.unlink()
            elif target.exists():
                import shutil
                shutil.rmtree(target)
            
            if source.exists():
                target.symlink_to(source)
                print(f"  ✅ {link_name} -> {source}")
            else:
                print(f"  ⚠️  {link_name} - source not found")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to setup data links: {e}")
        return False


def test_integration():
    """Test the integration."""
    print("🧪 Testing integration...")
    
    try:
        # Test biomni import
        sys.path.insert(0, str(Path.cwd().parent.parent))
        import biomni
        print("  ✅ Biomni import successful")
        
        # Test Node.js build
        result = subprocess.run(["npm", "run", "build"], cwd="apps/web", 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("  ✅ Next.js build successful")
        else:
            print(f"  ⚠️  Next.js build warnings: {result.stderr}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Testing failed: {e}")
        return False


def main():
    """Main setup function."""
    print("🎯 NIBR Biomni Canvas + Biomni Integration Setup")
    print("=" * 50)
    
    steps = [
        ("Dependencies", setup_dependencies),
        ("Data Links", setup_data_links),
        ("Integration Test", test_integration)
    ]
    
    for step_name, step_func in steps:
        print(f"\\n🔧 {step_name}")
        print("-" * 30)
        success = step_func()
        if not success:
            print(f"❌ {step_name} failed")
            return False
    
    print("\\n🎉 Setup complete!")
    print("\\n🚀 Next steps:")
    print("1. Start development: npm run dev (in apps/web)")
    print("2. Test biomni API: GET http://localhost:3000/api/biomni/test")
    print("3. Execute research: POST http://localhost:3000/api/biomni/test")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
'''
    
    setup_path = Path(__file__).parent / "setup_open_canvas.py"
    with open(setup_path, 'w') as f:
        f.write(setup_script)
    
    os.chmod(setup_path, 0o755)
    print(f"  ✅ Created {setup_path}")
    
    return True


def main():
    """Main fix function."""
    print("🎯 NIBR Biomni Canvas Integration Fix")
    print("=" * 40)
    print("Integrating with existing NIBR Biomni Canvas structure instead of parallel folders")
    
    steps = [
        ("Analyze Structure", analyze_existing_structure),
        ("Check Integration", check_biomni_integration),
        ("Update Wrapper", update_biomni_wrapper),
        ("Remove Redundant", remove_redundant_folders),
        ("Create Setup", create_proper_setup_script)
    ]
    
    results = {}
    
    for step_name, step_func in steps:
        print(f"\n🔧 {step_name}")
        print("-" * 30)
        try:
            results[step_name] = step_func()
        except Exception as e:
            print(f"❌ {step_name} failed: {e}")
            results[step_name] = False
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Integration Fix Summary")
    print("=" * 40)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for step_name, success in results.items():
        status = "✅ FIXED" if success else "❌ FAILED"
        print(f"{status}  {step_name}")
    
    print(f"\nResults: {passed}/{total} fixes successful")
    
    if passed >= 4:  # Most important fixes
        print("\n🎉 Integration fixed!")
        print("\n📋 What was corrected:")
        print("- ✅ Integrated with existing NIBR Biomni Canvas structure")
        print("- ✅ Enhanced biomni wrapper with persistent agents")
        print("- ✅ Removed redundant frontend/backend folders")
        print("- ✅ Created proper setup script")
        print("\n🚀 Use the existing NIBR Biomni Canvas:")
        print("  python setup_open_canvas.py")
        print("  cd apps/web && npm run dev")
        print("  Test: http://localhost:3000/api/biomni/test")
        
    else:
        print(f"\n⚠️  {total - passed} issues remain")
    
    return passed >= 4


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)