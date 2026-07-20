#!/bin/bash
#
# Multi-Agent Orchestration Platform - Linux Installer
# Version: 1.0.0
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation directory
INSTALL_DIR="/opt/multi-agent-platform"
DATA_DIR="/var/lib/multi-agent-platform"
LOG_DIR="/var/log/multi-agent-platform"
CONFIG_DIR="/etc/multi-agent-platform"
SERVICE_USER="multiagent"

# Print banner
print_banner() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║       Multi-Agent Orchestration Platform Installer        ║"
    echo "║                      Version 1.0.0                       ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}Error: This installer must be run as root${NC}"
        echo "Usage: sudo ./install.sh"
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    echo -e "${YELLOW}Checking system requirements...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is required${NC}"
        echo "Install with: sudo apt install python3 python3-pip python3-venv"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    echo -e "${GREEN}✓ Python ${PYTHON_VERSION}${NC}"
    
    # Check Node.js (optional for frontend build)
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        echo -e "${GREEN}✓ Node.js ${NODE_VERSION}${NC}"
        HAS_NODE=true
    else
        echo -e "${YELLOW}⚠ Node.js not found (frontend build will be skipped)${NC}"
        HAS_NODE=false
    fi
    
    # Check systemctl
    if command -v systemctl &> /dev/null; then
        echo -e "${GREEN}✓ systemd available${NC}"
        HAS_SYSTEMD=true
    else
        echo -e "${YELLOW}⚠ systemd not found (service installation will be skipped)${NC}"
        HAS_SYSTEMD=false
    fi
}

# Create service user
create_user() {
    echo -e "${YELLOW}Creating service user...${NC}"
    
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd -r -s /bin/false -d "$INSTALL_DIR" "$SERVICE_USER"
        echo -e "${GREEN}✓ Created user: ${SERVICE_USER}${NC}"
    else
        echo -e "${GREEN}✓ User ${SERVICE_USER} already exists${NC}"
    fi
}

# Create directories
create_directories() {
    echo -e "${YELLOW}Creating directories...${NC}"
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$CONFIG_DIR"
    
    echo -e "${GREEN}✓ Directories created${NC}"
}

# Copy application files
copy_files() {
    echo -e "${YELLOW}Copying application files...${NC}"
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    SOURCE_DIR="$(dirname "$SCRIPT_DIR")"
    
    # Copy backend
    cp -r "$SOURCE_DIR/backend" "$INSTALL_DIR/"
    cp -r "$SOURCE_DIR/src" "$INSTALL_DIR/"
    
    # Copy requirements
    cp "$SOURCE_DIR/backend/requirements.txt" "$INSTALL_DIR/requirements.txt"
    
    # Create data directory for database
    touch "$DATA_DIR/multi_agent.db"
    
    echo -e "${GREEN}✓ Files copied${NC}"
}

# Setup Python virtual environment
setup_venv() {
    echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
    
    python3 -m venv "$INSTALL_DIR/venv"
    source "$INSTALL_DIR/venv/bin/activate"
    
    # Install dependencies
    pip install --upgrade pip
    pip install -r "$INSTALL_DIR/requirements.txt"
    
    echo -e "${GREEN}✓ Virtual environment ready${NC}"
}

# Create configuration file
create_config() {
    echo -e "${YELLOW}Creating configuration...${NC}"
    
    # Generate a random secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    
    cat > "$CONFIG_DIR/config.env" << EOF
# Multi-Agent Platform Configuration

# Security
SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Database
DATABASE_URL=sqlite:////${DATA_DIR}/multi_agent.db

# Server
HOST=0.0.0.0
PORT=8000

# CORS (comma-separated origins)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:8080

# Logging
LOG_LEVEL=INFO
LOG_FILE=${LOG_DIR}/multi-agent.log
EOF
    
    chmod 600 "$CONFIG_DIR/config.env"
    
    echo -e "${GREEN}✓ Configuration created at ${CONFIG_DIR}/config.env${NC}"
}

# Create systemd service
create_service() {
    if [[ "$HAS_SYSTEMD" == true ]]; then
        echo -e "${YELLOW}Creating systemd service...${NC}"
        
        cat > /etc/systemd/system/multi-agent.service << EOF
[Unit]
Description=Multi-Agent Orchestration Platform API
After=network.target

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=${INSTALL_DIR}/venv/bin"
EnvironmentFile=${CONFIG_DIR}/config.env
ExecStart=${INSTALL_DIR}/venv/bin/python -m uvicorn backend.main:app --host \$HOST --port \$PORT
Restart=always
RestartSec=5

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${DATA_DIR} ${LOG_DIR}
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
        
        systemctl daemon-reload
        systemctl enable multi-agent.service
        
        echo -e "${GREEN}✓ Service created and enabled${NC}"
    fi
}

# Create CLI wrapper
create_cli() {
    echo -e "${YELLOW}Creating CLI commands...${NC}"
    
    cat > /usr/local/bin/multi-agent << 'EOF'
#!/bin/bash
INSTALL_DIR="/opt/multi-agent-platform"
source "$INSTALL_DIR/venv/bin/activate"

case "$1" in
    start)
        echo "Starting Multi-Agent Platform..."
        systemctl start multi-agent
        ;;
    stop)
        echo "Stopping Multi-Agent Platform..."
        systemctl stop multi-agent
        ;;
    restart)
        echo "Restarting Multi-Agent Platform..."
        systemctl restart multi-agent
        ;;
    status)
        systemctl status multi-agent
        ;;
    logs)
        journalctl -u multi-agent -f
        ;;
    shell)
        cd "$INSTALL_DIR"
        python3 -c "from backend.main import app; print('Backend loaded')"
        python3 -c "
from backend.database import engine, Base
from backend.models import User, Agent, Task
Base.metadata.create_all(bind=engine)
print('Database initialized')
"
        ;;
    *)
        echo "Multi-Agent Platform CLI"
        echo ""
        echo "Usage: multi-agent <command>"
        echo ""
        echo "Commands:"
        echo "  start    - Start the platform service"
        echo "  stop     - Stop the platform service"
        echo "  restart  - Restart the platform service"
        echo "  status   - Show service status"
        echo "  logs     - Show live logs"
        echo "  shell    - Initialize database"
        ;;
esac
EOF
    
    chmod +x /usr/local/bin/multi-agent
    
    echo -e "${GREEN}✓ CLI created at /usr/local/bin/multi-agent${NC}"
}

# Set permissions
set_permissions() {
    echo -e "${YELLOW}Setting permissions...${NC}"
    
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$DATA_DIR"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$LOG_DIR"
    chown "$SERVICE_USER:$SERVICE_USER" "$CONFIG_DIR/config.env"
    
    chmod 755 "$INSTALL_DIR"
    chmod 755 "$DATA_DIR"
    chmod 755 "$LOG_DIR"
    
    echo -e "${GREEN}✓ Permissions set${NC}"
}

# Print post-install instructions
print_post_install() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗"
    echo -e "║              Installation Complete!                       ║"
    echo -e "╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo ""
    echo "1. Start the service:"
    echo "   sudo multi-agent start"
    echo ""
    echo "2. Access the API:"
    echo "   http://localhost:8000"
    echo "   http://localhost:8000/docs (Swagger UI)"
    echo ""
    echo "3. Create your first user:"
    echo "   curl -X POST http://localhost:8000/api/auth/register \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"email\":\"admin@example.com\",\"username\":\"admin\",\"password\":\"secret\"}'"
    echo ""
    echo "4. View logs:"
    echo "   sudo multi-agent logs"
    echo ""
    echo -e "${YELLOW}Configuration: ${CONFIG_DIR}/config.env${NC}"
    echo -e "${YELLOW}Data directory: ${DATA_DIR}${NC}"
    echo -e "${YELLOW}Logs: ${LOG_DIR}/multi-agent.log${NC}"
    echo ""
}

# Main installation
main() {
    print_banner
    check_root
    check_requirements
    create_user
    create_directories
    copy_files
    setup_venv
    create_config
    create_service
    create_cli
    set_permissions
    print_post_install
}

main "$@"
