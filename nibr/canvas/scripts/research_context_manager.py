#!/usr/bin/env python3
"""
Research Context Manager for NIBR Biomni
Maintains research context across multiple executions for iterative research workflows
"""

import json
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import hashlib

class ResearchContextManager:
    """Manages research context and execution history for iterative workflows."""
    
    def __init__(self, agent_id: str, user_id: str, db_path: Optional[str] = None):
        self.agent_id = agent_id
        self.user_id = user_id
        self.db_path = db_path or f"/data/agents/{user_id}/context.db"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Load existing context
        self.context_chain = self._load_context_chain()
        self.execution_history = self._load_execution_history()
    
    def _init_database(self):
        """Initialize context database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Research sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_sessions (
                session_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                title TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Execution history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_history (
                execution_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                sequence_num INTEGER,
                prompt TEXT NOT NULL,
                response TEXT,
                context_used TEXT,
                tools_used TEXT,
                data_added TEXT,
                insights TEXT,
                artifacts TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES research_sessions(session_id)
            )
        """)
        
        # Context chain table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS context_chain (
                context_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                sequence_num INTEGER,
                context_type TEXT,
                context_data TEXT,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES research_sessions(session_id)
            )
        """)
        
        # Research artifacts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_artifacts (
                artifact_id TEXT PRIMARY KEY,
                execution_id TEXT NOT NULL,
                artifact_type TEXT,
                content TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (execution_id) REFERENCES execution_history(execution_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_session(self, title: str = None, description: str = None) -> str:
        """Create a new research session."""
        session_id = f"session_{self.agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO research_sessions (session_id, agent_id, user_id, title, description)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, self.agent_id, self.user_id, 
              title or "Research Session", 
              description or f"Research session started at {datetime.now()}"))
        
        conn.commit()
        conn.close()
        
        return session_id
    
    def add_execution(self, 
                     session_id: str,
                     prompt: str, 
                     response: str,
                     tools_used: List[str] = None,
                     data_added: Dict[str, str] = None,
                     insights: List[str] = None,
                     artifacts: List[Dict] = None) -> str:
        """Add an execution to the history with full context."""
        execution_id = hashlib.sha256(
            f"{session_id}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get sequence number
        cursor.execute(
            "SELECT MAX(sequence_num) FROM execution_history WHERE session_id = ?",
            (session_id,)
        )
        result = cursor.fetchone()
        sequence_num = (result[0] + 1) if result[0] else 1
        
        # Get context used
        context_summary = self.get_context_summary(session_id)
        
        # Insert execution
        cursor.execute("""
            INSERT INTO execution_history 
            (execution_id, session_id, sequence_num, prompt, response, 
             context_used, tools_used, data_added, insights, artifacts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            execution_id,
            session_id,
            sequence_num,
            prompt,
            response,
            context_summary,
            json.dumps(tools_used or []),
            json.dumps(data_added or {}),
            json.dumps(insights or []),
            json.dumps(artifacts or [])
        ))
        
        # Add to context chain
        self._add_to_context_chain(session_id, sequence_num, prompt, response)
        
        # Store artifacts
        if artifacts:
            for artifact in artifacts:
                self._store_artifact(execution_id, artifact)
        
        # Update session
        cursor.execute(
            "UPDATE research_sessions SET updated_at = ? WHERE session_id = ?",
            (datetime.now().isoformat(), session_id)
        )
        
        conn.commit()
        conn.close()
        
        # Update memory
        self.execution_history.append({
            'execution_id': execution_id,
            'prompt': prompt,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        
        return execution_id
    
    def _add_to_context_chain(self, session_id: str, sequence_num: int, 
                              prompt: str, response: str):
        """Add entry to context chain."""
        context_id = hashlib.sha256(
            f"{session_id}_{sequence_num}".encode()
        ).hexdigest()[:16]
        
        # Summarize if response is long
        summary = response[:500] if len(response) > 500 else response
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO context_chain 
            (context_id, session_id, sequence_num, context_type, context_data, summary)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            context_id,
            session_id,
            sequence_num,
            'execution',
            json.dumps({'prompt': prompt, 'response': response}),
            summary
        ))
        
        conn.commit()
        conn.close()
        
        # Update memory
        self.context_chain.append({
            'prompt': prompt,
            'response': response,
            'summary': summary,
            'sequence': sequence_num
        })
    
    def _store_artifact(self, execution_id: str, artifact: Dict):
        """Store research artifact."""
        artifact_id = hashlib.sha256(
            f"{execution_id}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO research_artifacts 
            (artifact_id, execution_id, artifact_type, content, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            artifact_id,
            execution_id,
            artifact.get('type', 'unknown'),
            artifact.get('content', ''),
            json.dumps(artifact.get('metadata', {}))
        ))
        
        conn.commit()
        conn.close()
    
    def get_context_prompt(self, new_prompt: str, session_id: str, 
                          max_context_items: int = 5) -> str:
        """Build a contextualized prompt including previous research."""
        # Get recent context
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT prompt, summary FROM context_chain 
            WHERE session_id = ? 
            ORDER BY sequence_num DESC 
            LIMIT ?
        """, (session_id, max_context_items))
        
        context_items = cursor.fetchall()
        conn.close()
        
        if not context_items:
            return new_prompt
        
        # Build context section
        context_parts = []
        for i, (prev_prompt, summary) in enumerate(reversed(context_items)):
            context_parts.append(f"""
Step {i+1} Query: {prev_prompt}
Key Findings: {summary}
""")
        
        # Construct contextualized prompt
        contextualized_prompt = f"""
PREVIOUS RESEARCH CONTEXT:
========================
{chr(10).join(context_parts)}

CURRENT RESEARCH TASK:
=====================
{new_prompt}

INSTRUCTIONS:
============
Please build upon the previous research findings above. Reference specific results, 
maintain consistency with prior analysis, and extend the investigation based on 
what has been discovered so far.
"""
        
        return contextualized_prompt
    
    def get_context_summary(self, session_id: str) -> str:
        """Get a summary of the research context."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get session info
        cursor.execute(
            "SELECT title, description FROM research_sessions WHERE session_id = ?",
            (session_id,)
        )
        session_info = cursor.fetchone()
        
        # Get execution count
        cursor.execute(
            "SELECT COUNT(*) FROM execution_history WHERE session_id = ?",
            (session_id,)
        )
        exec_count = cursor.fetchone()[0]
        
        # Get recent summaries
        cursor.execute("""
            SELECT summary FROM context_chain 
            WHERE session_id = ? 
            ORDER BY sequence_num DESC 
            LIMIT 3
        """, (session_id,))
        
        recent_summaries = cursor.fetchall()
        conn.close()
        
        summary = f"Session: {session_info[0] if session_info else 'Unknown'}\n"
        summary += f"Executions: {exec_count}\n"
        
        if recent_summaries:
            summary += "Recent findings:\n"
            for s in recent_summaries:
                summary += f"- {s[0][:100]}...\n"
        
        return summary
    
    def get_execution_history(self, session_id: str) -> List[Dict]:
        """Get full execution history for a session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT execution_id, sequence_num, prompt, response, 
                   tools_used, data_added, insights, created_at
            FROM execution_history 
            WHERE session_id = ? 
            ORDER BY sequence_num
        """, (session_id,))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'execution_id': row[0],
                'sequence': row[1],
                'prompt': row[2],
                'response': row[3],
                'tools_used': json.loads(row[4]) if row[4] else [],
                'data_added': json.loads(row[5]) if row[5] else {},
                'insights': json.loads(row[6]) if row[6] else [],
                'timestamp': row[7]
            })
        
        conn.close()
        return history
    
    def get_artifacts(self, execution_id: str = None, session_id: str = None) -> List[Dict]:
        """Get artifacts for an execution or session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if execution_id:
            cursor.execute("""
                SELECT artifact_id, artifact_type, content, metadata, created_at
                FROM research_artifacts 
                WHERE execution_id = ?
            """, (execution_id,))
        elif session_id:
            cursor.execute("""
                SELECT ra.artifact_id, ra.artifact_type, ra.content, 
                       ra.metadata, ra.created_at
                FROM research_artifacts ra
                JOIN execution_history eh ON ra.execution_id = eh.execution_id
                WHERE eh.session_id = ?
                ORDER BY ra.created_at DESC
            """, (session_id,))
        else:
            return []
        
        artifacts = []
        for row in cursor.fetchall():
            artifacts.append({
                'id': row[0],
                'type': row[1],
                'content': row[2],
                'metadata': json.loads(row[3]) if row[3] else {},
                'created_at': row[4]
            })
        
        conn.close()
        return artifacts
    
    def export_session_markdown(self, session_id: str) -> str:
        """Export entire research session as markdown."""
        # Get session info
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT title, description, created_at FROM research_sessions WHERE session_id = ?",
            (session_id,)
        )
        session_info = cursor.fetchone()
        conn.close()
        
        # Get execution history
        history = self.get_execution_history(session_id)
        
        # Build markdown
        md_parts = [
            f"# {session_info[0] if session_info else 'Research Session'}",
            f"",
            f"**Session ID**: {session_id}",
            f"**Created**: {session_info[2] if session_info else 'Unknown'}",
            f"**Description**: {session_info[1] if session_info else 'No description'}",
            f"",
            f"---",
            f""
        ]
        
        for exec_data in history:
            md_parts.extend([
                f"## Execution {exec_data['sequence']}",
                f"",
                f"**Timestamp**: {exec_data['timestamp']}",
                f"",
                f"### Query",
                f"```",
                exec_data['prompt'],
                f"```",
                f"",
                f"### Response",
                exec_data['response'],
                f""
            ])
            
            if exec_data['tools_used']:
                md_parts.extend([
                    f"### Tools Used",
                    f"- " + "\n- ".join(exec_data['tools_used']),
                    f""
                ])
            
            if exec_data['insights']:
                md_parts.extend([
                    f"### Key Insights",
                    f"- " + "\n- ".join(exec_data['insights']),
                    f""
                ])
            
            if exec_data['data_added']:
                md_parts.extend([
                    f"### Data Added",
                    f"```json",
                    json.dumps(exec_data['data_added'], indent=2),
                    f"```",
                    f""
                ])
            
            md_parts.append("---\n")
        
        return "\n".join(md_parts)
    
    def _load_context_chain(self) -> List[Dict]:
        """Load context chain from database."""
        # For memory efficiency, only load recent context
        return []
    
    def _load_execution_history(self) -> List[Dict]:
        """Load execution history from database."""
        # For memory efficiency, only load recent executions
        return []

# Example usage for protein connectivity validation scenario
if __name__ == "__main__":
    # Initialize context manager
    context_mgr = ResearchContextManager("agent_001", "researcher_001")
    
    # Create research session
    session_id = context_mgr.create_session(
        title="Protein Connectivity Analysis",
        description="Investigating protein-protein interactions in cancer pathways"
    )
    
    # First execution
    prompt1 = "Identify key proteins in DNA damage response pathway"
    response1 = "Found 20 key proteins including BRCA1, BRCA2, ATM..."
    
    context_mgr.add_execution(
        session_id=session_id,
        prompt=prompt1,
        response=response1,
        tools_used=["query_uniprot", "analyze_pathway"],
        insights=["BRCA1 is a critical hub protein"]
    )
    
    # Second execution with context
    prompt2 = "Validate connectivity of identified proteins"
    contextualized_prompt = context_mgr.get_context_prompt(prompt2, session_id)
    
    print("Contextualized Prompt:")
    print(contextualized_prompt)
    
    # Export session
    markdown = context_mgr.export_session_markdown(session_id)
    print("\nExported Markdown:")
    print(markdown[:500] + "...")