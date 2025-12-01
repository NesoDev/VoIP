#!/usr/bin/env bash
# ------------------------------------------------------------
#  start.sh – Construye y lanza los contenedores del proyecto
# ------------------------------------------------------------

# set -euo pipefail

# ── Colores ─────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() { echo -e "${BLUE}[INFO]${NC} $*"; }
print_ok()   { echo -e "${GREEN}[OK]${NC} $*"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
print_error(){ echo -e "${RED}[ERROR]${NC} $*"; }

spinner() {
    local pid=$1 delay=0.1 spin='|/-\\'
    while kill -0 "$pid" 2>/dev/null; do
        for ((i=0;i<${#spin};i++)); do
            printf "\r${YELLOW}[%c]${NC}" "${spin:$i:1}"
            sleep $delay
        done
    done
    printf "\r"
}

# ── Banner ─────────────────────────────────────────────────────
clear
cat <<'EOF' | sed "s/^/$(printf \"${BLUE}\")/;s/$/$(printf \"${NC}\")/"
╔══════════════════════════════════════════════════════════╗
║                VoIP Demo – Lanzamiento                 ║
╚══════════════════════════════════════════════════════════╝
EOF
echo

# ── Paso 1 – Parar contenedores existentes (si los hay) ───────
print_step "Deteniendo contenedores existentes..."
if docker compose version >/dev/null 2>&1; then
    docker compose down &>/dev/null || true
else
    docker-compose down &>/dev/null || true
fi
print_ok "Contenedores detenidos (si existían)."

# ── Paso 2 – Construir imágenes Docker ───────────────────────────
print_step "Construyendo imágenes Docker (puede tardar)..."
if docker compose version >/dev/null 2>&1; then
    docker compose build 2>&1 | while IFS= read -r line; do
        echo -e "${BLUE}[BUILD]${NC} $line"
    done
else
    docker-compose build 2>&1 | while IFS= read -r line; do
        echo -e "${BLUE}[BUILD]${NC} $line"
    done
fi
print_ok "Imágenes construidas."

# Detectar IP LAN para usarla como PUBLIC_IP si no estamos en AWS
# Esto se hace aquí para que PUBLIC_IP esté disponible para docker-compose
DETECTED_IP=$(ipconfig getifaddr en0 2>/dev/null || hostname -I | awk '{print $1}' 2>/dev/null || echo "127.0.0.1")
export PUBLIC_IP=${DETECTED_IP}

# ── Paso 3 – Iniciar contenedores ────────────────────────────────
print_step "Iniciando servicios..."
if docker compose version >/dev/null 2>&1; then
    if ! docker compose up -d; then
        print_error "Falló docker compose up"
        exit 1
    fi
else
    if ! docker-compose up -d; then
        print_error "Falló docker-compose up"
        exit 1
    fi
fi
print_ok "Servicios en marcha."

# ── Paso 4 – Esperar a que los contenedores estén listos ────────
print_step "Esperando a que los contenedores estén listos..."
sleep 5
print_ok "Listos."

# ── Paso 5 – Mostrar estado y puntos de acceso ───────────────────
echo
cat <<'EOF' | sed "s/^/$(printf \"${GREEN}\")/;s/$/$(printf \"${NC}\")/"
╔══════════════════════════════════════════════════════════╗
║                       Deploy finalizado                  ║
╚══════════════════════════════════════════════════════════╝
EOF

echo -e "${BLUE}Puntos de acceso:${NC}"
# Detectar IP pública (si se ejecuta en AWS)
if curl -s -m 5 http://169.254.169.254/latest/meta-data/public-ipv4 >/dev/null 2>&1; then
    PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
else
    PUBLIC_IP="localhost"
fi

# Detectar IP LAN para mostrarla si no estamos en AWS
DETECTED_IP=$(ipconfig getifaddr en0 2>/dev/null || hostname -I | awk '{print $1}' 2>/dev/null || echo "127.0.0.1")

if [[ "$PUBLIC_IP" == "localhost" ]]; then
    echo -e "  • Web Provisioning: ${GREEN}http://${DETECTED_IP}:3000${NC}"
    echo -e "  • Asterisk PBX:     ${GREEN}${DETECTED_IP}:5060 (UDP)${NC}"
else
    echo -e "  • Web Provisioning: ${GREEN}http://${PUBLIC_IP}:3000${NC}"
    echo -e "  • Asterisk PBX:     ${GREEN}${PUBLIC_IP}:5060 (UDP)${NC}"
    echo
    echo -e "${YELLOW}Puertos que deben estar abiertos en el firewall:${NC}"
    echo "  • TCP 3000  – Web UI"
    echo "  • UDP 5060  – SIP"
    echo "  • UDP 10000‑10100 – RTP"
fi

echo
echo -e "${BLUE}Comandos útiles:${NC}"
if docker compose version >/dev/null 2>&1; then
    echo -e "  • Ver logs:   ${GREEN}docker compose logs -f${NC}"
    echo -e "  • Detener:    ${GREEN}docker compose down${NC}"
    echo -e "  • Reiniciar:  ${GREEN}docker compose restart${NC}"
else
    echo -e "  • Ver logs:   ${GREEN}docker-compose logs -f${NC}"
    echo -e "  • Detener:    ${GREEN}docker-compose down${NC}"
    echo -e "  • Reiniciar:  ${GREEN}docker-compose restart${NC}"
fi

echo
