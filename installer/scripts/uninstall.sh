#!/bin/bash
#
# Multi-Agent Orchestration Platform - Uninstaller
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

INSTALL_DIR="/opt/multi-agent-platform"
DATA_DIR="/var/lib/multi-agent-platform"
LOG_DIR="/var/log/multi-agent-platform"
CONFIG_DIR="/etc/multi-agent-platform"
SERVICE_USER="multiagent"

echo -e "${YELLOW}Multi-Agent Platform Uninstaller${NC}"
echo ""

# Check root
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}Error: This uninstaller must be run as root${NC}"
    echo "Usage: sudo ./uninstall.sh"
    exit 1
fi

# Confirm
read -p "Are you sure you want to uninstall? (y/N): " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

echo -e "${YELLOW}Stopping service...${NC}"
if systemctl is-active --quiet multi-agent 2>/dev/null; then
    systemctl stop multi-agent
fi

if systemctl is-enabled --quiet multi-agent 2>/dev/null; then
    systemctl disable multi-agent
fi

echo -e "${YELLOW}Removing systemd service...${NC}"
rm -f /etc/systemd/system/multi-agent.service
systemctl daemon-reload 2>/dev/null || true

echo -e "${YELLOW}Removing CLI command...${NC}"
rm -f /usr/local/bin/multi-agent

echo -e "${YELLOW}Removing application files...${NC}"
rm -rf "$INSTALL_DIR"

echo -e "${YELLOW}Removing configuration...${NC}"
rm -rf "$CONFIG_DIR"

echo -e "${YELLOW}Removing logs...${NC}"
rm -rf "$LOG_DIR"

echo -e "${YELLOW}Removing data...${NC}"
read -p "Also delete database and data? (y/N): " delete_data
if [[ "$delete_data" == "y" || "$delete_data" == "Y" ]]; then
    rm -rf "$DATA_DIR"
    echo -e "${GREEN}✓ Data removed${NC}"
else
    echo -e "${YELLOW}Data preserved at ${DATA_DIR}${NC}"
fi

echo -e "${YELLOW}Removing service user...${NC}"
if id "$SERVICE_USER" &>/dev/null; then
    userdel "$SERVICE_USER" 2>/dev/null || true
fi

echo ""
echo -e "${GREEN}Uninstall complete!${NC}"
echo ""
