#!/usr/bin/env python3
"""
NIBR Biomni Canvas Backend Startup Script - Phase 1.5
Starts the FastAPI backend server for Canvas functionality
"""

import subprocess
import sys
import os
from pathlib import Path

def setup_backend():
    """Setup and start the backend server"""
    print("🚀 Starting NIBR Biomni Canvas Backend - Phase 1.5")
    
    # Navigate to backend directory
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    
    # Check if virtual environment exists
    venv_path = backend_dir / "venv"
    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
    
    # Determine python executable
    if sys.platform == "win32":
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"
    
    # Install requirements
    print("📚 Installing dependencies...")
    subprocess.run([str(pip_exe), "install", "-r", "requirements.txt"], check=True)
    
    # Set environment variables for development
    env = os.environ.copy()
    env["NODE_ENV"] = "development"
    env["PYTHONPATH"] = str(backend_dir)
    
    # Check for OpenAI API key
    if not env.get("OPENAI_API_KEY"):
        print("⚠️  No OPENAI_API_KEY found in environment.")
        print("   The backend will work with mock responses.")
        print("   To use ChatGPT, set OPENAI_API_KEY environment variable.")
    else:
        print("✅ OpenAI API key found - ChatGPT integration enabled")
    
    # Start the server
    print("🌐 Starting FastAPI server on http://localhost:54367")
    print("📊 Backend Dashboard: http://localhost:54367/docs")
    print("❤️  Health Check: http://localhost:54367/health")
    print("\n🎯 Phase 1.5: Canvas with ChatGPT integration")
    print("🔜 Next: Connect to Biomni agents in Phase 2")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        subprocess.run([
            str(python_exe), "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "54367", 
            "--reload"
        ], env=env, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped")

if __name__ == "__main__":
    setup_backend()
