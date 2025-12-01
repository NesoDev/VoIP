#!/bin/bash

set -e

echo "========================================="
echo "  VoIP Demo - Deployment Script"
echo "========================================="
echo ""

# Detect environment
echo "[1/6] Detecting environment..."
if curl -s -m 5 http://169.254.169.254/latest/meta-data/public-ipv4 &>/dev/null; then
    PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
    echo "      AWS environment detected"
    echo "      Public IP: $PUBLIC_IP"
else
    PUBLIC_IP="localhost"
    echo "      Local environment detected"
fi

echo ""
echo "[2/6] Configuring environment variables..."

cat > frontend/.env << EOF
NUXT_PUBLIC_API_BASE=http://${PUBLIC_IP}:8000
NUXT_PUBLIC_WS_BASE=ws://${PUBLIC_IP}:8000
EOF

echo "      API endpoint: http://${PUBLIC_IP}:8000"
echo "      WebSocket endpoint: ws://${PUBLIC_IP}:8000"
echo ""

# Verify Docker
echo "[3/6] Verifying Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "      ERROR: Docker not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "      ERROR: Docker Compose not installed"
    exit 1
fi

echo "      Docker verified"
echo ""

# Stop existing containers
echo "[4/6] Stopping existing containers..."
docker-compose down &>/dev/null || true
echo ""

# Build
echo "[5/6] Building Docker images..."
echo "      This may take several minutes on first run"
docker-compose build

echo ""
echo "[6/6] Starting services..."
docker-compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Verify status
echo ""
echo "Service Status:"
docker-compose ps

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
echo "  View logs:    docker-compose logs -f"
echo "  Stop:         docker-compose down"
echo "  Restart:      docker-compose restart"
echo ""
echo "========================================="
