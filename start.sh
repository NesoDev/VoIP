#!/bin/bash

set -e

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Print functions
print_step() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_result() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Spinner for long operations
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    while kill -0 $pid 2>/dev/null; do
        for (( i=0; i<${#spinstr}; i++ )); do
            printf "\r${YELLOW}[%c]${NC}" "${spinstr:$i:1}"
            sleep $delay
        done
    done
    printf "\r"
}

# Installation functions
install_docker() {
    print_step "  └─ Adding Docker repository..."
    (sudo apt-get update -qq && \
     sudo apt-get install -y -qq ca-certificates curl gnupg lsb-release && \
     sudo mkdir -p /etc/apt/keyrings && \
     curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
     echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
     sudo tee /etc/apt/sources.list.d/docker.list > /dev/null) &>/dev/null &
    spinner $!
    wait $!
    
    print_step "  └─ Installing Docker Engine..."
    (sudo apt-get update -qq && \
     sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin) &>/dev/null &
    spinner $!
    wait $!
    
    print_step "  └─ Configuring Docker permissions..."
    sudo usermod -aG docker $USER
    
    print_result "Docker installed successfully"
}

install_docker_compose() {
    print_step "  └─ Installing Docker Compose..."
    (sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose && \
     sudo chmod +x /usr/local/bin/docker-compose) &>/dev/null &
    spinner $!
    wait $!
    
    print_result "Docker Compose installed successfully"
}

# Banner
clear
echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║              VoIP Demo - Deployment Script               ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Step 1: Environment detection
print_step "Detecting environment..."
if curl -s -m 5 http://169.254.169.254/latest/meta-data/public-ipv4 &>/dev/null; then
    PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
    print_result "AWS environment detected - Public IP: $PUBLIC_IP"
else
    PUBLIC_IP="localhost"
    print_result "Local environment detected"
fi

# Step 2: Docker verification
print_step "Checking Docker installation..."

DOCKER_MISSING=false
COMPOSE_MISSING=false

if ! command -v docker &> /dev/null; then
    print_warning "Docker not found"
    DOCKER_MISSING=true
else
    DOCKER_VERSION=$(docker --version | cut -d ' ' -f3 | sed 's/,//')
    print_result "Docker found - Version: $DOCKER_VERSION"
fi

if docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version --short 2>/dev/null || echo "unknown")
    print_result "Docker Compose found - Version: $COMPOSE_VERSION"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | cut -d ' ' -f3 | sed 's/,//')
    print_result "Docker Compose found - Version: $COMPOSE_VERSION"
else
    print_warning "Docker Compose not found"
    COMPOSE_MISSING=true
fi

# Step 3: Install if needed
if [ "$DOCKER_MISSING" = true ] || [ "$COMPOSE_MISSING" = true ]; then
    echo ""
    echo -e "${YELLOW}Missing components detected${NC}"
    echo ""
    echo -n -e "${YELLOW}Install missing components? [y/N]:${NC} "
    read -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        print_step "Installing dependencies..."
        
        if [ "$DOCKER_MISSING" = true ]; then
            install_docker
        fi
        
        if [ "$COMPOSE_MISSING" = true ] && [ "$DOCKER_MISSING" = false ]; then
            install_docker_compose
        fi
        
        if [ "$DOCKER_MISSING" = true ]; then
            print_warning "Docker group permissions require logout/login"
            print_warning "Attempting to apply permissions for this session..."
            echo ""
        fi
    else
        echo ""
        print_error "Installation cancelled"
        echo ""
        echo -e "${BLUE}Manual installation:${NC}"
        echo "  sudo apt-get update"
        echo "  sudo apt-get install -y docker.io docker-compose"
        echo ""
        exit 1
    fi
fi

# Step 4: Environment configuration
print_step "Configuring environment variables..."
mkdir -p frontend

cat > frontend/.env << EOF
API_BASE=http://${PUBLIC_IP}:8000
WS_BASE=ws://${PUBLIC_IP}:8000
EOF

print_result "Configuration saved"

# Step 5: Stop existing containers
print_step "Stopping existing containers..."
if docker compose version &> /dev/null 2>&1; then
    docker compose down &>/dev/null || true
else
    docker-compose down &>/dev/null || true
fi
print_result "Cleanup complete"

# Step 6: Build images
print_step "Building Docker images (this may take several minutes)..."
if docker compose version &> /dev/null 2>&1; then
    (docker compose build) &>/dev/null &
else
    (docker-compose build) &>/dev/null &
fi
spinner $!
wait $!
print_result "Images built successfully"

# Step 7: Start services
print_step "Starting services..."
if docker compose version &> /dev/null 2>&1; then
    (docker compose up -d) &>/dev/null &
else
    (docker-compose up -d) &>/dev/null &
fi
spinner $!
wait $!
print_result "Services started"

# Step 8: Wait for services
print_step "Waiting for services to be ready..."
sleep 5
print_result "Services ready"

# Final status
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                          ║${NC}"
echo -e "${GREEN}║              ✓ Deployment Complete                       ║${NC}"
echo -e "${GREEN}║                                                          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}Access Points:${NC}"
if [ "$PUBLIC_IP" = "localhost" ]; then
    echo -e "  • Frontend:    ${GREEN}http://localhost:3000${NC}"
    echo -e "  • Backend API: ${GREEN}http://localhost:8000${NC}"
else
    echo -e "  • Frontend:    ${GREEN}http://${PUBLIC_IP}:3000${NC}"
    echo -e "  • Backend API: ${GREEN}http://${PUBLIC_IP}:8000${NC}"
    echo ""
    echo -e "${YELLOW}Required Firewall Ports:${NC}"
    echo "  • TCP 3000 (Frontend)"
    echo "  • TCP 8000 (Backend API)"
    echo "  • UDP 5060 (SIP Signaling)"
    echo "  • UDP 10000-10100 (RTP Audio)"
fi

echo ""
echo -e "${BLUE}Common Commands:${NC}"
if docker compose version &> /dev/null 2>&1; then
    echo -e "  • View logs:  ${GREEN}docker compose logs -f${NC}"
    echo -e "  • Stop:       ${GREEN}docker compose down${NC}"
    echo -e "  • Restart:    ${GREEN}docker compose restart${NC}"
else
    echo -e "  • View logs:  ${GREEN}docker-compose logs -f${NC}"
    echo -e "  • Stop:       ${GREEN}docker-compose down${NC}"
    echo -e "  • Restart:    ${GREEN}docker-compose restart${NC}"
fi
echo ""

if [ "$DOCKER_MISSING" = true ]; then
    echo -e "${YELLOW}⚠ IMPORTANT:${NC}"
    echo "  You must logout and login again to apply Docker group changes."
    echo -e "  Execute: ${BLUE}exit${NC} and reconnect."
    echo ""
fi
