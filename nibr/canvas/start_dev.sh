#!/bin/bash
# NIBR Biomni Canvas - Development Startup

echo "🚀 Starting NIBR Biomni Canvas (Development)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command_exists python3; then
    echo "${RED}❌ Python 3 not found${NC}"
    exit 1
fi

if ! command_exists node; then
    echo "${RED}❌ Node.js not found${NC}"
    exit 1
fi

echo "${GREEN}✅ Prerequisites check passed${NC}"

# Set environment variables
export PYTHONPATH="${PWD}/backend/app:${PYTHONPATH}"
export DEBUG=true
export LOG_LEVEL=DEBUG

# Create data directories
mkdir -p backend/data/{agents,datalake,canvas,exports}

# Start backend in background
echo "🔧 Starting backend server..."
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "${GREEN}✅ Backend server started successfully${NC}"
else
    echo "${RED}❌ Backend server failed to start${NC}"
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
echo "${GREEN}🎉 NIBR Biomni Canvas is running!${NC}"
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
trap 'echo "\n🛑 Stopping services..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0' INT
wait
