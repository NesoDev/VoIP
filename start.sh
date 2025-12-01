#!/bin/bash

set -e

echo "========================================="
echo "  VoIP Demo - Deployment Script"
echo "========================================="
echo ""

# Function to install Docker on Ubuntu
install_docker() {
    echo ""
    echo "Installing Docker..."
    
    # Update package index
    sudo apt-get update
    
    # Install prerequisites
    sudo apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # Add Docker's official GPG key
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Set up repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Update package index
    sudo apt-get update
    
    # Install Docker Engine
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    
    echo ""
    echo "Docker installed successfully!"
    echo "Note: You may need to log out and back in for group changes to take effect."
    echo "      Alternatively, run: newgrp docker"
    echo ""
}

# Function to install Docker Compose standalone
install_docker_compose() {
    echo ""
    echo "Installing Docker Compose..."
    
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    
    sudo chmod +x /usr/local/bin/docker-compose
    
    echo "Docker Compose installed successfully!"
    echo ""
}

# Detect environment
echo "[1/7] Detecting environment..."
if curl -s -m 5 http://169.254.169.254/latest/meta-data/public-ipv4 &>/dev/null; then
    PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
    echo "      AWS environment detected"
    echo "      Public IP: $PUBLIC_IP"
else
    PUBLIC_IP="localhost"
    echo "      Local environment detected"
fi

echo ""
echo "[2/7] Checking Docker installation..."

DOCKER_MISSING=false
COMPOSE_MISSING=false

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "      Docker not found"
    DOCKER_MISSING=true
else
    echo "      Docker found: $(docker --version)"
fi

# Check Docker Compose (try both plugin and standalone)
if docker compose version &> /dev/null; then
    echo "      Docker Compose found: $(docker compose version)"
elif command -v docker-compose &> /dev/null; then
    echo "      Docker Compose found: $(docker-compose --version)"
else
    echo "      Docker Compose not found"
    COMPOSE_MISSING=true
fi

# Install if missing
if [ "$DOCKER_MISSING" = true ] || [ "$COMPOSE_MISSING" = true ]; then
    echo ""
    echo "Missing components detected."
    echo ""
    
    read -p "Would you like to install the missing components? (y/n): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ "$DOCKER_MISSING" = true ]; then
            install_docker
        fi
        
        if [ "$COMPOSE_MISSING" = true ] && [ "$DOCKER_MISSING" = false ]; then
            install_docker_compose
        fi
        
        echo "Installation complete. Continuing with deployment..."
        
        # Apply group changes without logout
        if [ "$DOCKER_MISSING" = true ]; then
            echo ""
            echo "Applying Docker group permissions..."
            newgrp docker <<EOF
            exec "$0" "$@"
EOF
            exit 0
        fi
    else
        echo ""
        echo "Installation cancelled. Please install Docker manually:"
        echo "  sudo apt-get update"
        echo "  sudo apt-get install -y docker.io docker-compose"
        echo ""
        exit 1
    fi
fi

echo ""
echo "[3/7] Configuring environment variables..."

# Create frontend directory if it doesn't exist
mkdir -p frontend

cat > frontend/.env << EOF
API_BASE=http://${PUBLIC_IP}:8000
WS_BASE=ws://${PUBLIC_IP}:8000
EOF

echo "      API endpoint: http://${PUBLIC_IP}:8000"
echo "      WebSocket endpoint: ws://${PUBLIC_IP}:8000"
echo ""

# Stop existing containers
echo "[4/7] Stopping existing containers..."
if docker compose version &> /dev/null; then
    docker compose down &>/dev/null || true
else
    docker-compose down &>/dev/null || true
fi
echo ""

# Build
echo "[5/7] Building Docker images..."
echo "      This may take several minutes on first run"
if docker compose version &> /dev/null; then
    docker compose build
else
    docker-compose build
fi

echo ""
echo "[6/7] Starting services..."
if docker compose version &> /dev/null; then
    docker compose up -d
else
    docker-compose up -d
fi

echo ""
echo "[7/7] Waiting for services to be ready..."
sleep 10

# Verify status
echo ""
echo "Service Status:"
if docker compose version &> /dev/null; then
    docker compose ps
else
    docker-compose ps
fi

echo ""
echo "========================================="
echo "  Deployment Complete"
echo "========================================="
echo ""
echo "Access Points:"
echo ""
if [ "$PUBLIC_IP" = "localhost" ]; then
    echo "  Frontend: http://localhost:3000"
    echo "  Backend API: http://localhost:8000"
else
    echo "  Frontend: http://${PUBLIC_IP}:3000"
    echo "  Backend API: http://${PUBLIC_IP}:8000"
    echo ""
    echo "Required Firewall Ports:"
    echo "  - TCP 3000 (Frontend)"
    echo "  - TCP 8000 (Backend API)"
    echo "  - UDP 5060 (SIP Signaling)"
    echo "  - UDP 10000-10100 (RTP Audio)"
fi

echo ""
echo "Common Commands:"
if docker compose version &> /dev/null; then
    echo "  View logs:    docker compose logs -f"
    echo "  Stop:         docker compose down"
    echo "  Restart:      docker compose restart"
else
    echo "  View logs:    docker-compose logs -f"
    echo "  Stop:         docker-compose down"
    echo "  Restart:      docker-compose restart"
fi
echo ""
echo "========================================="
