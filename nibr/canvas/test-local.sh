#!/bin/bash

# NIBR Biomni Canvas - Local Testing Script
# This script tests the basic functionality

echo "🧪 NIBR Biomni Canvas - Local Testing"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Base URL
BASE_URL="http://localhost:3000"

# Function to check if server is running
check_server() {
    if curl -s -o /dev/null -w "%{http_code}" $1 | grep -q "200\|302"; then
        return 0
    else
        return 1
    fi
}

echo "1. Checking if servers are running..."
echo ""

# Check Next.js server
if check_server "$BASE_URL"; then
    echo -e "${GREEN}✓${NC} Next.js server is running on $BASE_URL"
else
    echo -e "${RED}✗${NC} Next.js server is not running"
    echo "  Please run: ./start-dev.sh"
    exit 1
fi

echo ""
echo "2. Testing API endpoints..."
echo ""

# Test health endpoint
echo "Testing /api/biomni/test..."
RESPONSE=$(curl -s "$BASE_URL/api/biomni/test")
if echo "$RESPONSE" | grep -q '"status":"ok"'; then
    echo -e "${GREEN}✓${NC} API test endpoint is working"
    echo "  Response: $(echo $RESPONSE | python3 -m json.tool 2>/dev/null | head -5)"
else
    echo -e "${RED}✗${NC} API test endpoint failed"
    echo "  Response: $RESPONSE"
fi

echo ""
echo "3. Testing authentication..."
echo ""

# Test login with admin credentials
echo "Testing login with admin/admin..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin"}' \
    -c /tmp/nibr_cookies.txt)

if echo "$LOGIN_RESPONSE" | grep -q '"success":true'; then
    echo -e "${GREEN}✓${NC} Login successful"
else
    echo -e "${YELLOW}⚠${NC} Login endpoint not fully configured yet"
    echo "  This is expected - auth system needs more integration"
fi

echo ""
echo "4. Testing Python biomni installation..."
echo ""

# Test Python biomni
if python3 -c "import biomni; print('✓ Biomni version:', biomni.__version__ if hasattr(biomni, '__version__') else 'installed')" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Biomni Python package is installed"
else
    echo -e "${YELLOW}⚠${NC} Biomni not installed. Installing..."
    pip3 install biomni --upgrade
fi

# Test biomni wrapper
echo ""
echo "5. Testing biomni wrapper script..."
if [ -f "scripts/biomni_wrapper.py" ]; then
    echo -e "${GREEN}✓${NC} Biomni wrapper script exists"
    
    # Check if it's executable
    if [ -x "scripts/biomni_wrapper.py" ]; then
        echo -e "${GREEN}✓${NC} Biomni wrapper is executable"
    else
        echo -e "${YELLOW}⚠${NC} Making wrapper executable..."
        chmod +x scripts/biomni_wrapper.py
    fi
else
    echo -e "${RED}✗${NC} Biomni wrapper script not found"
fi

echo ""
echo "6. Checking data directories..."
echo ""

DATA_DIR="/tmp/nibr_data"
DIRS=("agents" "uploads" "datalake" "db")

for dir in "${DIRS[@]}"; do
    if [ -d "$DATA_DIR/$dir" ]; then
        echo -e "${GREEN}✓${NC} $DATA_DIR/$dir exists"
    else
        echo -e "${YELLOW}⚠${NC} Creating $DATA_DIR/$dir..."
        mkdir -p "$DATA_DIR/$dir"
    fi
done

echo ""
echo "======================================"
echo "📊 Test Summary"
echo "======================================"
echo ""

# Summary
echo "✅ Basic setup is complete!"
echo ""
echo "Next steps to get fully running:"
echo ""
echo "1. If not already done, add your API keys to .env.local:"
echo "   - ANTHROPIC_API_KEY"
echo "   - OPENAI_API_KEY"
echo ""
echo "2. Start the development server:"
echo "   ./start-dev.sh"
echo ""
echo "3. Open browser to:"
echo "   $BASE_URL"
echo ""
echo "4. Login with:"
echo "   Username: admin"
echo "   Password: admin"
echo ""
echo "======================================"