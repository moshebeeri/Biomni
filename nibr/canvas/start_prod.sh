#!/bin/bash
# NIBR Biomni Canvas - Production Startup

echo "🚀 Starting NIBR Biomni Canvas (Production)"

# Set environment variables
export PYTHONPATH="${PWD}/backend/app:${PYTHONPATH}"
export DEBUG=false
export LOG_LEVEL=INFO

# Load environment variables if .env exists
if [ -f backend/config/.env ]; then
    source backend/config/.env
fi

# Create data directories
mkdir -p backend/data/{agents,datalake,canvas,exports}

# Build frontend if not already built
if [ ! -d "frontend/build" ]; then
    echo "🏗️  Building frontend..."
    cd frontend && npm run build && cd ..
fi

# Start backend
echo "🔧 Starting production backend server..."
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
