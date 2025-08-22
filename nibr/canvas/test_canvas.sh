#!/bin/bash
# Quick test script for Canvas

echo "🧪 Running Canvas integration test..."

# Test backend
echo "Testing backend..."
python3 backend/setup_phase1.py --check-only

# Test frontend compilation
echo "Testing frontend..."
cd frontend && npx tsc --noEmit

echo "✅ Canvas integration test complete"
