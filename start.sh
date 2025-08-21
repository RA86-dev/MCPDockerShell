#!/bin/bash

# MCPDocker Enhanced - Quick Start Script
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 MCPDocker Enhanced - Quick Start${NC}"
echo "======================================"

# Check if dependencies are installed
if [ ! -f "requirements-simple.txt" ]; then
    echo -e "${YELLOW}⚠️ Using basic requirements.txt${NC}"
    REQUIREMENTS_FILE="requirements.txt"
else
    REQUIREMENTS_FILE="requirements-simple.txt"
fi

# Install dependencies if needed
echo -e "${BLUE}📦 Checking dependencies...${NC}"
python3 -c "import mcp, docker, fastapi" 2>/dev/null || {
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip3 install -r "$REQUIREMENTS_FILE"
}

# Create basic directories
mkdir -p logs data config backups documentation

echo -e "${GREEN}✅ Setup complete!${NC}"
echo
echo -e "${BLUE}🎯 Starting MCPDocker Enhanced...${NC}"
echo -e "${BLUE}📊 Server will be available at: http://localhost:8080${NC}"
echo -e "${BLUE}⚙️ Configuration UI: http://localhost:8081${NC}"
echo -e "${YELLOW}⏹️ Press Ctrl+C to stop${NC}"
echo

# Start the server
exec python3 main.py "$@"