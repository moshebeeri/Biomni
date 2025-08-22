#!/usr/bin/env python3
"""
NIBR Biomni Wrapper for Canvas Integration
Provides a bridge between Node.js Canvas and Python Biomni A1 agent
Now uses PersistentA1 and GlobalAgentManager for state persistence
"""

import sys
import json
import asyncio
import sqlite3
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import inspect
import traceback

# Add path to nibr/src for PersistentA1 and GlobalAgentManager
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

# Ensure biomni is importable
try:
    from biomni.agent import A1
except ImportError:
    print(json.dumps({
        'type': 'error',
        'message': 'Biomni not installed. Please run: pip install biomni'
    }))
    sys.exit(1)

# Import persistent agent components
try:
    from persistent_a1 import PersistentA1
    from global_agent_manager import agent_manager
except ImportError as e:
    # Fallback to regular A1 if PersistentA1 not available
    print(json.dumps({
        'type': 'warning',
        'message': f'PersistentA1 not available, using regular A1: {str(e)}'
    }))
    PersistentA1 = A1
    agent_manager = None

# Import research context manager
try:
    from research_context_manager import ResearchContextManager
except ImportError:
    ResearchContextManager = None

class BiomniWrapper:
    """Wrapper class for Biomni A1 agent with persistence and streaming support."""
    
    def __init__(self, agent_id: str, user_id: str):
        self.agent_id = agent_id
        self.user_id = user_id
        self.agent = None
        self.db_path = f"/data/agents/{user_id}/agent_state.db"
        
        # Ensure directories exist
        os.makedirs(f"/data/agents/{user_id}/data", exist_ok=True)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize context manager if available
        self.context_manager = None
        if ResearchContextManager:
            self.context_manager = ResearchContextManager(agent_id, user_id)
        
        # Current session
        self.current_session_id = None
        
        self.initialize_agent()
    
    def initialize_agent(self):
        """Initialize PersistentA1 agent with persistence using GlobalAgentManager."""
        try:
            # Use GlobalAgentManager if available, otherwise create PersistentA1 directly
            if agent_manager:
                # Use GlobalAgentManager to get or create persistent agent
                self.agent = agent_manager.get_agent(
                    agent_id=self.agent_id,
                    path=f"/data/agents/{self.user_id}/data",
                    llm=os.getenv("BIOMNI_LLM", "claude-3-5-sonnet-20241022"),
                    use_tool_retriever=True,
                    timeout_seconds=600
                )
                
                # Send message about using GlobalAgentManager
                self.send_message({
                    'type': 'info',
                    'message': f'Using GlobalAgentManager for agent {self.agent_id}'
                })
            else:
                # Create PersistentA1 directly (or A1 if PersistentA1 not available)
                self.agent = PersistentA1(
                    agent_id=self.agent_id,
                    path=f"/data/agents/{self.user_id}/data",
                    llm=os.getenv("BIOMNI_LLM", "claude-3-5-sonnet-20241022"),
                    use_tool_retriever=True,
                    timeout_seconds=600
                )
            
            # No need to load state manually - PersistentA1 handles it automatically
            # But keep backward compatibility with SQLite state for migration
            if not isinstance(self.agent, PersistentA1):
                # Only load SQLite state if using regular A1
                self.load_agent_state()
            
            # Send initialization success
            self.send_message({
                'type': 'initialized',
                'agent_id': self.agent_id,
                'status': 'ready',
                'agent_type': type(self.agent).__name__
            })
            
        except Exception as e:
            self.send_message({
                'type': 'error',
                'message': f'Failed to initialize agent: {str(e)}'
            })
            sys.exit(1)
    
    def load_agent_state(self):
        """Load agent state from SQLite."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_state (
                    agent_id TEXT PRIMARY KEY,
                    custom_tools TEXT,
                    custom_data TEXT,
                    custom_software TEXT,
                    research_context TEXT,
                    updated_at TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tool_library (
                    tool_name TEXT PRIMARY KEY,
                    tool_code TEXT,
                    tool_description TEXT,
                    created_at TIMESTAMP
                )
            """)
            
            # Load agent state
            cursor.execute(
                "SELECT * FROM agent_state WHERE agent_id = ?",
                (self.agent_id,)
            )
            
            state = cursor.fetchone()
            if state:
                # Restore custom tools
                if state[1]:  # custom_tools
                    tools = json.loads(state[1])
                    for tool_name, tool_info in tools.items():
                        if 'code' in tool_info:
                            self._restore_tool_from_code(tool_info['code'])
                
                # Restore custom data
                if state[2]:  # custom_data
                    data = json.loads(state[2])
                    if hasattr(self.agent, 'add_data'):
                        self.agent.add_data(data)
                
                # Restore custom software
                if state[3]:  # custom_software
                    software = json.loads(state[3])
                    if hasattr(self.agent, 'add_software'):
                        self.agent.add_software(software)
            
            conn.close()
            
        except Exception as e:
            self.send_message({
                'type': 'warning',
                'message': f'Could not load agent state: {str(e)}'
            })
    
    def save_agent_state(self):
        """Save agent state - handled automatically by PersistentA1."""
        try:
            # If using PersistentA1, state is saved automatically
            if isinstance(self.agent, PersistentA1):
                # PersistentA1 handles its own state persistence
                # Just trigger a save to ensure it's up to date
                if hasattr(self.agent, '_save_persistent_state'):
                    self.agent._save_persistent_state()
                    self.send_message({
                        'type': 'debug',
                        'message': 'State saved via PersistentA1'
                    })
                return
            
            # Fallback to SQLite for regular A1 (backward compatibility)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Serialize custom tools
            custom_tools = {}
            if hasattr(self.agent, '_custom_tools'):
                for name, func in self.agent._custom_tools.items():
                    try:
                        custom_tools[name] = {
                            'name': name,
                            'code': inspect.getsource(func),
                            'doc': func.__doc__ or ''
                        }
                    except:
                        # If we can't get source, store a placeholder
                        custom_tools[name] = {
                            'name': name,
                            'code': f"# Tool {name} - source not available",
                            'doc': func.__doc__ or ''
                        }
            
            # Get custom data and software
            custom_data = {}
            if hasattr(self.agent, '_custom_data'):
                custom_data = dict(self.agent._custom_data)
            
            custom_software = {}
            if hasattr(self.agent, '_custom_software'):
                custom_software = dict(self.agent._custom_software)
            
            # Save or update state
            cursor.execute("""
                INSERT OR REPLACE INTO agent_state 
                (agent_id, custom_tools, custom_data, custom_software, research_context, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                self.agent_id,
                json.dumps(custom_tools),
                json.dumps(custom_data),
                json.dumps(custom_software),
                f"NIBR Research Agent {self.agent_id}",
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.send_message({
                'type': 'warning',
                'message': f'Could not save agent state: {str(e)}'
            })
    
    def _restore_tool_from_code(self, code: str):
        """Restore a tool from source code."""
        try:
            exec_globals = {}
            exec(code, exec_globals)
            
            # Find the function in executed code
            for name, obj in exec_globals.items():
                if callable(obj) and not name.startswith('_'):
                    if hasattr(self.agent, 'add_tool'):
                        self.agent.add_tool(obj)
                    break
        except Exception as e:
            self.send_message({
                'type': 'warning',
                'message': f'Could not restore tool: {str(e)}'
            })
    
    def send_message(self, message: Dict[str, Any]):
        """Send JSON message to Node.js process."""
        print(json.dumps(message))
        sys.stdout.flush()
    
    async def handle_execute(self, prompt: str, use_context: bool = True):
        """Execute research task with streaming."""
        try:
            # Initialize session if needed
            if self.context_manager and not self.current_session_id:
                self.current_session_id = self.context_manager.create_session(
                    title="Research Session",
                    description=f"Started at {datetime.now()}"
                )
            
            # Apply context if available and requested
            contextualized_prompt = prompt
            if use_context and self.context_manager and self.current_session_id:
                contextualized_prompt = self.context_manager.get_context_prompt(
                    prompt, self.current_session_id
                )
                
                # Send context notification
                self.send_message({
                    'type': 'context_applied',
                    'original_prompt': prompt,
                    'contextualized': True,
                    'session_id': self.current_session_id
                })
            
            step_count = 0
            full_response = []
            tools_used = []
            insights_found = []
            artifacts_created = []
            
            # Use go_stream for streaming execution
            for step in self.agent.go_stream(contextualized_prompt):
                step_count += 1
                
                # Parse step for relevant information
                step_content = step.get('output', '')
                full_response.append(step_content)
                
                output = {
                    'type': 'step',
                    'step_number': step_count,
                    'content': step_content,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Detect tool execution
                if 'tool' in step:
                    tool_name = step['tool']
                    tools_used.append(tool_name)
                    output['tool_execution'] = {
                        'name': tool_name,
                        'status': 'executing',
                        'category': self._categorize_tool(tool_name)
                    }
                
                # Detect code in output
                if '```python' in step_content:
                    code = self._extract_code(step_content)
                    if code:
                        artifact = {
                            'type': 'code',
                            'language': 'python',
                            'content': code
                        }
                        artifacts_created.append(artifact)
                        output['code_artifact'] = artifact
                
                # Detect potential insights
                if self._is_insight(step_content):
                    insight = self._extract_insight(step_content)
                    insights_found.append(insight)
                    output['insight'] = insight
                
                # Send step update
                self.send_message(output)
            
            # Save state after execution
            self.save_agent_state()
            
            # Save to context manager if available
            complete_response = '\n'.join(full_response)
            if self.context_manager and self.current_session_id:
                execution_id = self.context_manager.add_execution(
                    session_id=self.current_session_id,
                    prompt=prompt,
                    response=complete_response,
                    tools_used=list(set(tools_used)),
                    insights=insights_found,
                    artifacts=artifacts_created
                )
                
                # Send context saved notification
                self.send_message({
                    'type': 'context_saved',
                    'session_id': self.current_session_id,
                    'execution_id': execution_id
                })
            
            # Send completion message
            self.send_message({
                'type': 'complete',
                'total_steps': step_count,
                'status': 'success',
                'tools_used': list(set(tools_used)),
                'insights_count': len(insights_found),
                'artifacts_count': len(artifacts_created),
                'session_id': self.current_session_id
            })
            
        except Exception as e:
            self.send_message({
                'type': 'error',
                'message': f'Execution failed: {str(e)}',
                'traceback': traceback.format_exc()
            })
    
    async def handle_add_tool(self, code: str, name: str, description: str = ""):
        """Add custom tool to agent."""
        try:
            # Execute the code to get the function
            exec_globals = {}
            exec(code, exec_globals)
            
            # Find the callable function
            tool_func = None
            for obj_name, obj in exec_globals.items():
                if callable(obj) and not obj_name.startswith('_'):
                    tool_func = obj
                    break
            
            if tool_func:
                # Add to agent
                if hasattr(self.agent, 'add_tool'):
                    self.agent.add_tool(tool_func)
                
                # Save to tool library
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO tool_library 
                    (tool_name, tool_code, tool_description, created_at)
                    VALUES (?, ?, ?, ?)
                """, (name, code, description, datetime.now().isoformat()))
                conn.commit()
                conn.close()
                
                # Save agent state
                self.save_agent_state()
                
                self.send_message({
                    'type': 'tool_added',
                    'name': name,
                    'status': 'success'
                })
            else:
                self.send_message({
                    'type': 'error',
                    'message': 'No callable function found in provided code'
                })
                
        except Exception as e:
            self.send_message({
                'type': 'error',
                'message': f'Failed to add tool: {str(e)}'
            })
    
    async def handle_add_data(self, path: str, description: str):
        """Add data to agent context."""
        try:
            if hasattr(self.agent, 'add_data'):
                self.agent.add_data({path: description})
                self.save_agent_state()
                
                self.send_message({
                    'type': 'data_added',
                    'path': path,
                    'description': description,
                    'status': 'success'
                })
            else:
                self.send_message({
                    'type': 'error',
                    'message': 'Agent does not support add_data method'
                })
                
        except Exception as e:
            self.send_message({
                'type': 'error',
                'message': f'Failed to add data: {str(e)}'
            })
    
    async def handle_list_tools(self):
        """List all available tools."""
        try:
            tools = []
            
            # Get built-in tools
            if hasattr(self.agent, 'tool_registry'):
                for tool_name in self.agent.tool_registry.tools.keys():
                    tools.append({
                        'name': tool_name,
                        'type': 'built-in',
                        'category': self._categorize_tool(tool_name)
                    })
            
            # Get custom tools
            if hasattr(self.agent, '_custom_tools'):
                for tool_name in self.agent._custom_tools.keys():
                    tools.append({
                        'name': tool_name,
                        'type': 'custom',
                        'category': 'user-defined'
                    })
            
            # If using PersistentA1, also list tools from list_custom_tools
            if isinstance(self.agent, PersistentA1) and hasattr(self.agent, 'list_custom_tools'):
                persistent_tools = self.agent.list_custom_tools()
                for tool_name in persistent_tools:
                    if not any(t['name'] == tool_name for t in tools):
                        tools.append({
                            'name': tool_name,
                            'type': 'custom-persistent',
                            'category': 'user-defined'
                        })
            
            self.send_message({
                'type': 'tools_list',
                'tools': tools,
                'total': len(tools)
            })
            
        except Exception as e:
            self.send_message({
                'type': 'error',
                'message': f'Failed to list tools: {str(e)}'
            })
    
    async def handle_list_agents(self):
        """List all available agents via GlobalAgentManager."""
        try:
            if agent_manager:
                agents = agent_manager.list_agents()
                agent_details = []
                for agent_id in agents:
                    info = agent_manager.get_agent_info(agent_id)
                    if info:
                        agent_details.append({
                            'agent_id': agent_id,
                            'is_loaded': info.get('is_loaded', False),
                            'created_at': info.get('created_at'),
                            'last_accessed': info.get('last_accessed'),
                            'tools_count': info.get('tools_count', 0),
                            'data_count': info.get('data_count', 0)
                        })
                
                self.send_message({
                    'type': 'agents_list',
                    'agents': agent_details,
                    'total': len(agent_details)
                })
            else:
                self.send_message({
                    'type': 'agents_list',
                    'agents': [{'agent_id': self.agent_id, 'is_loaded': True}],
                    'total': 1,
                    'note': 'GlobalAgentManager not available'
                })
        except Exception as e:
            self.send_message({
                'type': 'error',
                'message': f'Failed to list agents: {str(e)}'
            })
    
    async def handle_clone_agent(self, source_id: str, target_id: str):
        """Clone an agent using GlobalAgentManager."""
        try:
            if agent_manager:
                cloned_agent = agent_manager.clone_agent(source_id, target_id)
                if cloned_agent:
                    self.send_message({
                        'type': 'agent_cloned',
                        'source_id': source_id,
                        'target_id': target_id,
                        'status': 'success'
                    })
                else:
                    self.send_message({
                        'type': 'error',
                        'message': f'Failed to clone agent {source_id} to {target_id}'
                    })
            else:
                self.send_message({
                    'type': 'error',
                    'message': 'GlobalAgentManager not available'
                })
        except Exception as e:
            self.send_message({
                'type': 'error',
                'message': f'Failed to clone agent: {str(e)}'
            })
    
    async def handle_get_agent_info(self):
        """Get current agent information."""
        try:
            info = {
                'agent_id': self.agent_id,
                'agent_type': type(self.agent).__name__,
                'user_id': self.user_id
            }
            
            # Add PersistentA1 specific info
            if isinstance(self.agent, PersistentA1) and hasattr(self.agent, 'get_state_summary'):
                state_summary = self.agent.get_state_summary()
                info.update(state_summary)
            
            # Add GlobalAgentManager info if available
            if agent_manager:
                manager_info = agent_manager.get_agent_info(self.agent_id)
                if manager_info:
                    info['manager_info'] = manager_info
            
            self.send_message({
                'type': 'agent_info',
                'info': info
            })
        except Exception as e:
            self.send_message({
                'type': 'error',
                'message': f'Failed to get agent info: {str(e)}'
            })
    
    def _categorize_tool(self, tool_name: str) -> str:
        """Categorize tool based on name patterns."""
        categories = {
            'query_': 'Database Query',
            'analyze_': 'Analysis',
            'predict_': 'Prediction',
            'design_': 'Design',
            'screen_': 'Screening',
            'blast_': 'Sequence Analysis',
            'pcr_': 'Molecular Biology',
            'annotate_': 'Annotation'
        }
        
        for prefix, category in categories.items():
            if tool_name.startswith(prefix):
                return category
        return 'General'
    
    def _extract_code(self, text: str) -> Optional[str]:
        """Extract Python code from markdown text."""
        import re
        pattern = r'```python\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)
        return matches[0] if matches else None
    
    def _is_insight(self, text: str) -> bool:
        """Check if text contains an insight."""
        insight_keywords = [
            'found', 'discovered', 'identified', 'conclusion',
            'suggests', 'indicates', 'reveals', 'shows'
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in insight_keywords)
    
    def _extract_insight(self, text: str) -> str:
        """Extract insight from text."""
        # Simple extraction - take the sentence with insight keyword
        sentences = text.split('.')
        for sentence in sentences:
            if self._is_insight(sentence):
                return sentence.strip() + '.'
        return text[:200]  # Return first 200 chars as fallback
    
    async def handle_message(self, message: Dict[str, Any]):
        """Handle incoming message from Node.js."""
        msg_type = message.get('type')
        
        if msg_type == 'execute':
            await self.handle_execute(message.get('prompt', ''))
        
        elif msg_type == 'add_tool':
            await self.handle_add_tool(
                message.get('code', ''),
                message.get('name', 'custom_tool'),
                message.get('description', '')
            )
        
        elif msg_type == 'add_data':
            await self.handle_add_data(
                message.get('path', ''),
                message.get('description', '')
            )
        
        elif msg_type == 'list_tools':
            await self.handle_list_tools()
        
        elif msg_type == 'list_agents':
            await self.handle_list_agents()
        
        elif msg_type == 'clone_agent':
            await self.handle_clone_agent(
                message.get('source_id', ''),
                message.get('target_id', '')
            )
        
        elif msg_type == 'get_agent_info':
            await self.handle_get_agent_info()
        
        elif msg_type == 'ping':
            self.send_message({'type': 'pong'})
        
        else:
            self.send_message({
                'type': 'error',
                'message': f'Unknown message type: {msg_type}'
            })
    
    def run(self):
        """Main loop to handle messages from Node.js."""
        self.send_message({
            'type': 'ready',
            'agent_id': self.agent_id,
            'user_id': self.user_id
        })
        
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                message = json.loads(line.strip())
                asyncio.run(self.handle_message(message))
                
            except json.JSONDecodeError as e:
                self.send_message({
                    'type': 'error',
                    'message': f'Invalid JSON: {str(e)}'
                })
            except EOFError:
                break
            except Exception as e:
                self.send_message({
                    'type': 'error',
                    'message': f'Unexpected error: {str(e)}',
                    'traceback': traceback.format_exc()
                })

def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print(json.dumps({
            'type': 'error',
            'message': 'Usage: biomni_wrapper.py <agent_id> <user_id>'
        }))
        sys.exit(1)
    
    agent_id = sys.argv[1]
    user_id = sys.argv[2]
    
    wrapper = BiomniWrapper(agent_id, user_id)
    wrapper.run()

if __name__ == "__main__":
    main()