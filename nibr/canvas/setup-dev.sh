#!/bin/bash

# NIBR Biomni Canvas - Local Development Setup Script
# This script sets up the environment for running on local Mac

echo "🚀 NIBR Biomni Canvas - Local Development Setup"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Step 1: Check prerequisites
echo ""
echo "1. Checking prerequisites..."

if ! command_exists node; then
    print_error "Node.js is not installed. Please install Node.js 18+ first."
    exit 1
else
    print_status "Node.js found: $(node --version)"
fi

if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.9+ first."
    exit 1
else
    print_status "Python found: $(python3 --version)"
fi

if ! command_exists yarn; then
    print_warning "Yarn not found. Installing yarn..."
    npm install -g yarn
else
    print_status "Yarn found: $(yarn --version)"
fi

# Step 2: Create local data directories
echo ""
echo "2. Creating local data directories..."

# Use /tmp for local development (on Mac)
DATA_DIR="/tmp/nibr_data"
mkdir -p "$DATA_DIR/agents"
mkdir -p "$DATA_DIR/uploads"
mkdir -p "$DATA_DIR/datalake"
mkdir -p "$DATA_DIR/db"

print_status "Created data directories at $DATA_DIR"

# Step 3: Set up environment variables
echo ""
echo "3. Setting up environment variables..."

# Copy example env if it doesn't exist
if [ ! -f .env.local ]; then
    cat > .env.local << EOF
# NIBR Biomni Canvas - Local Development Environment

# Authentication (Local Dev)
AD_SERVER=ldaps://mock.ad.server
AD_DOMAIN=NIBR.LOCAL
ADMIN_PASSWORD=admin
MOCK_AD=true

# Database (Local)
DATABASE_PATH=$DATA_DIR/db/nibr_canvas.db

# Session
SESSION_SECRET=local-dev-secret-key
SESSION_TIMEOUT_HOURS=8

# Biomni Configuration
# Add your API keys here
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# Local paths
BIOMNI_DATA_PATH=$DATA_DIR/biomni
BIOMNI_CACHE_PATH=$DATA_DIR/biomni_cache
UPLOAD_PATH=$DATA_DIR/uploads

# Application
NODE_ENV=development
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Legacy Supabase vars (kept for compatibility)
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=not-used
SUPABASE_SERVICE_ROLE_KEY=not-used

# LangGraph
LANGGRAPH_API_URL=http://localhost:54367

# NIBR Specific
NIBR_ENVIRONMENT=local-dev
NIBR_ENABLE_LOGGING=true

# Python
PYTHONPATH=$PWD/scripts:$PYTHONPATH
EOF
    print_status "Created .env.local file"
    print_warning "Please add your ANTHROPIC_API_KEY and OPENAI_API_KEY to .env.local"
else
    print_status ".env.local already exists"
fi

# Step 4: Install dependencies
echo ""
echo "4. Installing dependencies..."

# Install yarn dependencies
yarn install

print_status "Dependencies installed"

# Step 5: Install Python dependencies
echo ""
echo "5. Installing Python dependencies..."

# Check if biomni is installed
if ! python3 -c "import biomni" 2>/dev/null; then
    print_warning "Biomni not installed. Installing..."
    pip3 install biomni --upgrade
else
    print_status "Biomni is already installed"
fi

# Install other Python dependencies
pip3 install better-sqlite3 python-dotenv

print_status "Python dependencies installed"

# Step 6: Make Python script executable
chmod +x scripts/biomni_wrapper.py
print_status "Made biomni_wrapper.py executable"

# Step 7: Create startup script
echo ""
echo "7. Creating startup script..."

cat > start-dev.sh << 'EOF'
#!/bin/bash

# Load environment variables
export $(cat .env.local | grep -v '^#' | xargs)

# Set Python path
export PYTHONPATH="$PWD/scripts:$PYTHONPATH"

# Set data path for local dev
export DATA_PATH="/tmp/nibr_data"

echo "Starting NIBR Biomni Canvas in development mode..."
echo "================================================"
echo ""
echo "📌 Access Points:"
echo "   • Frontend: http://localhost:3000"
echo "   • API Docs: http://localhost:3000/api"
echo "   • LangGraph: http://localhost:54367"
echo ""
echo "🔐 Login Credentials:"
echo "   • Username: admin"
echo "   • Password: admin"
echo ""
echo "📁 Data Directory: $DATA_PATH"
echo ""
echo "Starting services..."

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down services..."
    kill $LANGGRAPH_PID 2>/dev/null
    kill $NEXT_PID 2>/dev/null
    exit 0
}

trap cleanup INT TERM

# Start LangGraph server in background
cd apps/agents
yarn dev &
LANGGRAPH_PID=$!
cd ../..

# Wait a bit for LangGraph to start
sleep 3

# Start Next.js dev server
cd apps/web
yarn dev &
NEXT_PID=$!
cd ../..

echo ""
echo "✅ Services started!"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for processes
wait $LANGGRAPH_PID $NEXT_PID
EOF

chmod +x start-dev.sh
print_status "Created start-dev.sh script"

# Step 8: Final instructions
echo ""
echo "================================================"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Add your API keys to .env.local:"
echo "   - ANTHROPIC_API_KEY"
echo "   - OPENAI_API_KEY"
echo ""
echo "2. Start the development server:"
echo "   ./start-dev.sh"
echo ""
echo "3. Open http://localhost:3000 in your browser"
echo ""
echo "4. Login with:"
echo "   Username: admin"
echo "   Password: admin"
echo ""
echo "================================================"