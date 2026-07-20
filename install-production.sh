#!/bin/bash
#
# Multi-Agent Platform - Production Installer
#

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║       Multi-Agent Platform - Production Setup             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is required${NC}"
        echo "Install: curl -fsSL https://get.docker.com | sh"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker found${NC}"
    
    if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Error: Docker Compose is required${NC}"
        echo "Install: sudo apt install docker-compose-plugin"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker Compose found${NC}"
}

# Generate secrets
generate_secrets() {
    echo -e "${YELLOW}Generating secure secrets...${NC}"
    
    SECRET_KEY=$(openssl rand -hex 32)
    POSTGRES_PASSWORD=$(openssl rand -base64 32)
    
    cat > .env << EOF
# Generated secrets - DO NOT COMMIT
SECRET_KEY=${SECRET_KEY}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
GRAFANA_PASSWORD=$(openssl rand -base64 16)

# Database
DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/multiagent

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Environment
ENVIRONMENT=production
DEBUG=false
EOF
    
    chmod 600 .env
    echo -e "${GREEN}✓ Secrets generated${NC}"
}

# Setup SSL certificates
setup_ssl() {
    echo -e "${YELLOW}Setting up SSL certificates...${NC}"
    
    mkdir -p docker/ssl
    
    if [ ! -f docker/ssl/cert.pem ]; then
        # Generate self-signed certificate for development
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout docker/ssl/key.pem \
            -out docker/ssl/cert.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        echo -e "${GREEN}✓ Self-signed SSL certificate generated${NC}"
    else
        echo -e "${GREEN}✓ SSL certificates exist${NC}"
    fi
}

# Create Docker network
setup_network() {
    echo -e "${YELLOW}Setting up Docker network...${NC}"
    
    docker network create multi-agent-net 2>/dev/null || true
    echo -e "${GREEN}✓ Network ready${NC}"
}

# Build and start services
start_services() {
    echo -e "${YELLOW}Building and starting services...${NC}"
    
    cd docker
    
    # Build images
    docker compose -f docker-compose.prod.yml build
    
    # Start all services
    docker compose -f docker-compose.prod.yml up -d
    
    cd ..
    
    echo -e "${GREEN}✓ Services started${NC}"
}

# Wait for services
wait_for_services() {
    echo -e "${YELLOW}Waiting for services to be ready...${NC}"
    
    # Wait for database
    echo -n "Waiting for PostgreSQL"
    for i in {1..30}; do
        if docker exec multi-agent-db pg_isready -U postgres &>/dev/null; then
            echo -e " ${GREEN}✓${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    # Wait for Redis
    echo -n "Waiting for Redis"
    for i in {1..15}; do
        if docker exec multi-agent-redis redis-cli ping &>/dev/null; then
            echo -e " ${GREEN}✓${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    # Wait for API
    echo -n "Waiting for API"
    for i in {1..30}; do
        if curl -s http://localhost/health &>/dev/null; then
            echo -e " ${GREEN}✓${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done
}

# Print summary
print_summary() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗"
    echo -e "║         Installation Complete!                            ║"
    echo -e "╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Services:${NC}"
    echo "  API:          https://localhost"
    echo "  API Docs:     https://localhost/docs"
    echo "  Grafana:      http://localhost:3000"
    echo "  Prometheus:   http://localhost:9090"
    echo ""
    echo -e "${BLUE}Default Credentials:${NC}"
    echo "  Grafana: admin / $(grep GRAFANA_PASSWORD .env | cut -d= -f2)"
    echo ""
    echo -e "${YELLOW}Quick Commands:${NC}"
    echo "  cd docker"
    echo "  docker compose -f docker-compose.prod.yml ps      # Status"
    echo "  docker compose -f docker-compose.prod.yml logs -f # Logs"
    echo "  docker compose -f docker-compose.prod.yml down    # Stop"
    echo ""
    echo -e "${YELLOW}Note:${NC} Update docker/nginx.conf with your SSL certificates"
    echo "      for production use."
    echo ""
}

# Main installation
main() {
    check_prerequisites
    generate_secrets
    setup_ssl
    setup_network
    start_services
    wait_for_services
    print_summary
}

main "$@"
