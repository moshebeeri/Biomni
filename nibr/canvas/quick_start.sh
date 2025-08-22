#!/bin/bash
# Quick Start Script for NIBR Biomni Canvas

echo "🚀 Quick Start - NIBR Biomni Canvas"

# Set Python path to include biomni
export PYTHONPATH="${PWD}/backend/app:${PWD}/../..:${PYTHONPATH}"

# Start backend
echo "Starting backend..."
cd backend && python -m uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Wait for backend
sleep 3

# Check backend health
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend started successfully"
else
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start frontend
echo "Starting frontend..."
cd ../frontend && npm start &
FRONTEND_PID=$!

echo ""
echo "🎉 Canvas is starting!"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend: http://localhost:8000"  
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "👤 Login: researcher / researcher"
echo ""
echo "Press Ctrl+C to stop"

trap 'echo "\nStopping..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0' INT
wait
