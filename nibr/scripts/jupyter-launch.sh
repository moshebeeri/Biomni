#!/bin/bash

# Convenience script to access Biomni NIBR Jupyter Lab

echo "================================================"
echo "   🚀 BIOMNI NIBR JUPYTER LAB"
echo "================================================"
echo ""

# Check if container is running
if ! docker ps | grep -q biomni-nibr; then
    echo "❌ Container 'biomni-nibr' is not running!"
    echo ""
    echo "Start it with:"
    echo "  cd nibr/scripts && ./setup.sh --jupyter"
    exit 1
fi

# Check if Jupyter is running
if docker exec biomni-nibr pgrep jupyter > /dev/null; then
    echo "✅ Jupyter is running (no authentication required)"
    echo ""
    echo "Access at:"
    echo "  🌐 http://localhost:8888"
    echo ""
    echo "No token or password needed!"
else
    echo "⚠️  Jupyter is not running. Starting it now..."
    docker exec -d biomni-nibr jupyter lab \
        --ip=0.0.0.0 \
        --port=8888 \
        --no-browser \
        --allow-root \
        --NotebookApp.token='' \
        --NotebookApp.password='' \
        --LabApp.token='' \
        --LabApp.password=''
    
    sleep 3
    echo "✅ Jupyter started (no authentication required)"
    echo ""
    echo "Access at:"
    echo "  🌐 http://localhost:8888"
fi

echo ""
echo "📓 Quick start notebook:"
echo "  notebooks/biomni_nibr_quickstart.ipynb"
echo ""
echo "To stop Jupyter: docker exec biomni-nibr pkill jupyter"
echo ""

# Try to open browser (works on Mac)
if command -v open > /dev/null; then
    echo "Opening browser..."
    open http://localhost:8888
fi