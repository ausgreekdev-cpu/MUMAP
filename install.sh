#!/bin/bash
#
# Multi-Agent Platform - Quick Install
# Usage: bash install.sh
#

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║       Multi-Agent Platform Installer                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check for Docker
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker found${NC}"
    
    echo -e "${YELLOW}Starting with Docker...${NC}"
    
    # Create data directory
    mkdir -p data logs
    
    # Build and run
    docker-compose up -d --build
    
    echo ""
    echo -e "${GREEN}✓ Platform is running!${NC}"
    echo ""
    echo "  API:      http://localhost:8000"
    echo "  API Docs: http://localhost:8000/docs"
    echo ""
    echo "  Stop:     docker-compose down"
    echo "  Logs:     docker-compose logs -f"
    echo ""
    
elif command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓ Python found${NC}"
    echo -e "${YELLOW}Docker not found, installing locally...${NC}"
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Install dependencies
    pip install -r backend/requirements.txt
    
    # Create data directory
    mkdir -p data logs
    
    # Start server
    echo -e "${GREEN}✓ Starting server...${NC}"
    echo ""
    echo "  API:      http://localhost:8000"
    echo "  API Docs: http://localhost:8000/docs"
    echo ""
    
    cd backend
    python -m uvicorn main:app --reload --port 8000
    
else
    echo "Error: Python 3 or Docker is required"
    echo "Install one of them and try again"
    exit 1
fi
