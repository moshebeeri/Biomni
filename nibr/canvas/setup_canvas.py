#!/usr/bin/env python3
"""
Complete Canvas Setup Script
Sets up both frontend and backend for NIBR Biomni Canvas
"""

import os
import sys
import subprocess
import json
from pathlib import Path
import time


def run_command(command, cwd=None, check=True, capture_output=False):
    """Run shell command with error handling."""
    print(f"Running: {command}")
    if cwd:
        print(f"  in directory: {cwd}")
    
    if capture_output:
        result = subprocess.run(
            command, shell=True, check=check, 
            capture_output=True, text=True, cwd=cwd
        )
        return result.stdout.strip()
    else:
        result = subprocess.run(command, shell=True, check=check, cwd=cwd)
        return result.returncode == 0


def setup_backend():
    """Setup backend dependencies and configuration."""
    print("🔧 Setting up backend...")
    
    backend_dir = Path(__file__).parent / "backend"
    
    try:
        # Install Python dependencies
        print("Installing Python dependencies...")
        run_command(f"{sys.executable} -m pip install fastapi uvicorn websockets python-multipart pyjwt bcrypt aiofiles pydantic", cwd=backend_dir)
        
        # Install State Management Foundation dependencies
        print("Installing State Management Foundation dependencies...")
        run_command(f"{sys.executable} -m pip install dill cloudpickle", cwd=backend_dir)
        
        # Setup data symbolic links
        print("Setting up data symbolic links...")
        run_command(f"{sys.executable} ../setup_data_links.py", cwd=backend_dir)
        
        # Run State Management Foundation setup if it exists
        state_setup = backend_dir / "setup_state_foundation.py"
        if state_setup.exists():
            print("Running State Management Foundation setup...")
            run_command(f"{sys.executable} setup_state_foundation.py", cwd=backend_dir)
        
        print("✅ Backend setup complete")
        return True
        
    except Exception as e:
        print(f"❌ Backend setup failed: {e}")
        return False


def setup_frontend():
    """Setup frontend dependencies."""
    print("🎨 Setting up frontend...")
    
    frontend_dir = Path(__file__).parent / "frontend"
    
    try:
        # Check if Node.js is available
        try:
            node_version = run_command("node --version", capture_output=True)
            print(f"✅ Node.js {node_version}")
        except:
            print("❌ Node.js not found. Please install Node.js 16+ from https://nodejs.org/")
            return False
        
        # Install npm dependencies with legacy peer deps to resolve conflicts
        print("Installing npm dependencies...")
        run_command("npm install --legacy-peer-deps", cwd=frontend_dir)
        
        print("✅ Frontend setup complete")
        return True
        
    except Exception as e:
        print(f"❌ Frontend setup failed: {e}")
        return False


def test_backend():
    """Test backend functionality."""
    print("🧪 Testing backend...")
    
    backend_dir = Path(__file__).parent / "backend"
    
    try:
        # Test imports
        print("Testing Python imports...")
        sys.path.insert(0, str(backend_dir / "app"))
        
        # Add biomni to path
        biomni_path = str(Path(__file__).parent.parent.parent)
        if biomni_path not in sys.path:
            sys.path.insert(0, biomni_path)
        
        # Test State Management Foundation
        try:
            from biomni.persistent_agent import GlobalAgentManager, PersistentA1
            print("✅ State Management Foundation imports working")
        except ImportError as e:
            print(f"❌ State Management Foundation import failed: {e}")
            return False
        
        # Test main application
        try:
            from main import app
            print("✅ Main application imports working")
        except ImportError as e:
            print(f"❌ Main application import failed: {e}")
            return False
        
        # Test authentication
        try:
            from auth.ad_auth import ADAuthProvider
            print("✅ Authentication module working")
        except ImportError as e:
            print(f"❌ Authentication import failed: {e}")
            return False
        
        print("✅ Backend tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        return False


def test_frontend():
    """Test frontend compilation."""
    print("🧪 Testing frontend...")
    
    frontend_dir = Path(__file__).parent / "frontend"
    
    try:
        # Test TypeScript compilation
        print("Testing TypeScript compilation...")
        result = run_command("npx tsc --noEmit", cwd=frontend_dir, check=False)
        
        if result:
            print("✅ TypeScript compilation successful")
        else:
            print("⚠️  TypeScript compilation has warnings (check output)")
        
        # Test build (quick check)
        print("Testing build process...")
        run_command("npm run build", cwd=frontend_dir)
        
        build_dir = frontend_dir / "build"
        if build_dir.exists():
            print("✅ Frontend build successful")
            return True
        else:
            print("❌ Frontend build failed")
            return False
        
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
        return False


def create_startup_scripts():
    """Create startup scripts for development and production."""
    print("📜 Creating startup scripts...")
    
    base_dir = Path(__file__).parent
    
    # Development startup script
    dev_script = f"""#!/bin/bash
# NIBR Biomni Canvas - Development Startup

echo "🚀 Starting NIBR Biomni Canvas (Development)"

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

# Function to check if command exists
command_exists() {{
    command -v "$1" >/dev/null 2>&1
}}

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command_exists python3; then
    echo "${{RED}}❌ Python 3 not found${{NC}}"
    exit 1
fi

if ! command_exists node; then
    echo "${{RED}}❌ Node.js not found${{NC}}"
    exit 1
fi

echo "${{GREEN}}✅ Prerequisites check passed${{NC}}"

# Set environment variables
export PYTHONPATH="${{PWD}}/backend/app:${{PWD}}/../..:${{PYTHONPATH}}"
export DEBUG=true
export LOG_LEVEL=DEBUG

# Create data directories
mkdir -p backend/data/{{agents,datalake,canvas,exports}}

# Start backend in background
echo "🔧 Starting backend server..."
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "${{GREEN}}✅ Backend server started successfully${{NC}}"
else
    echo "${{RED}}❌ Backend server failed to start${{NC}}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start frontend
echo "🎨 Starting frontend server..."
cd ../frontend
npm start &
FRONTEND_PID=$!

# Wait a bit for frontend to start
sleep 5

echo ""
echo "${{GREEN}}🎉 NIBR Biomni Canvas is running!${{NC}}"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "❤️  Health Check: http://localhost:8000/health"
echo ""
echo "👤 Demo login: researcher / researcher"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for Ctrl+C
trap 'echo "\\n🛑 Stopping services..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0' INT
wait
"""
    
    with open(base_dir / "start_dev.sh", 'w') as f:
        f.write(dev_script)
    os.chmod(base_dir / "start_dev.sh", 0o755)
    
    # Production startup script
    prod_script = f"""#!/bin/bash
# NIBR Biomni Canvas - Production Startup

echo "🚀 Starting NIBR Biomni Canvas (Production)"

# Set environment variables
export PYTHONPATH="${{PWD}}/backend/app:${{PWD}}/../..:${{PYTHONPATH}}"
export DEBUG=false
export LOG_LEVEL=INFO

# Load environment variables if .env exists
if [ -f backend/config/.env ]; then
    source backend/config/.env
fi

# Create data directories
mkdir -p backend/data/{{agents,datalake,canvas,exports}}

# Build frontend if not already built
if [ ! -d "frontend/build" ]; then
    echo "🏗️  Building frontend..."
    cd frontend && npm run build && cd ..
fi

# Start backend
echo "🔧 Starting production backend server..."
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
"""
    
    with open(base_dir / "start_prod.sh", 'w') as f:
        f.write(prod_script)
    os.chmod(base_dir / "start_prod.sh", 0o755)
    
    # Quick test script
    test_script = f"""#!/bin/bash
# Quick test script for Canvas

echo "🧪 Running Canvas integration test..."

# Test backend
echo "Testing backend..."
python3 backend/setup_phase1.py --check-only

# Test frontend compilation
echo "Testing frontend..."
cd frontend && npx tsc --noEmit

echo "✅ Canvas integration test complete"
"""
    
    with open(base_dir / "test_canvas.sh", 'w') as f:
        f.write(test_script)
    os.chmod(base_dir / "test_canvas.sh", 0o755)
    
    print("✅ Startup scripts created:")
    print(f"  - start_dev.sh   (development mode)")
    print(f"  - start_prod.sh  (production mode)")
    print(f"  - test_canvas.sh (quick test)")
    
    return True


def create_configuration():
    """Create configuration files."""
    print("⚙️ Creating configuration...")
    
    backend_dir = Path(__file__).parent / "backend"
    config_dir = backend_dir / "config"
    config_dir.mkdir(exist_ok=True)
    
    # Create .env.example
    env_example = """# NIBR Biomni Canvas Environment Variables

# Authentication
JWT_SECRET_KEY=change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=8

# Active Directory (optional)
AD_ENABLED=false
AD_SERVER=ldaps://ad.nibr.novartis.com
AD_DOMAIN=NIBR.NOVARTIS.COM

# Database
DATABASE_PATH=./data/canvas.db
AGENT_STATE_DIR=./data/agents

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true
LOG_LEVEL=INFO

# Canvas
MAX_WEBSOCKET_CONNECTIONS=100
SESSION_TIMEOUT_HOURS=8
"""
    
    with open(config_dir / ".env.example", 'w') as f:
        f.write(env_example)
    
    print("✅ Configuration files created")
    return True


def main():
    """Main setup function."""
    print("🎯 NIBR Biomni Canvas Complete Setup")
    print("=" * 50)
    
    steps = [
        ("Backend Setup", setup_backend),
        ("Frontend Setup", setup_frontend), 
        ("Backend Testing", test_backend),
        ("Frontend Testing", test_frontend),
        ("Configuration", create_configuration),
        ("Startup Scripts", create_startup_scripts)
    ]
    
    results = {}
    
    for step_name, step_func in steps:
        try:
            print(f"\\n{'='*20} {step_name} {'='*20}")
            results[step_name] = step_func()
        except KeyboardInterrupt:
            print("\\n❌ Setup cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"❌ {step_name} failed with exception: {e}")
            results[step_name] = False
    
    # Summary
    print("\\n" + "=" * 50)
    print("📊 Canvas Setup Summary")
    print("=" * 50)
    
    passed = 0
    total = len(steps)
    
    for step_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}  {step_name}")
        if success:
            passed += 1
    
    print(f"\\nResults: {passed}/{total} steps completed successfully")
    
    if passed == total:
        print("\\n🎉 NIBR Biomni Canvas setup complete!")
        print("\\n🚀 Quick Start:")
        print("1. Start development servers: ./start_dev.sh")
        print("2. Open browser: http://localhost:3000") 
        print("3. Login with: researcher / researcher")
        print("\\n📚 Documentation:")
        print("- Backend: backend/README_PHASE1_CANVAS_INTEGRATION.md")
        print("- API Docs: http://localhost:8000/docs (when running)")
        print("- Health: http://localhost:8000/health (when running)")
        
        return True
    else:
        print(f"\\n⚠️  Setup incomplete ({total - passed} failures)")
        print("Please review the errors above and retry.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
