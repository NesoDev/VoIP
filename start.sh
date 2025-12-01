#!/usr/bin/env bash
# ------------------------------------------------------------
#  start.sh – Construye y lanza los contenedores del proyecto
# ------------------------------------------------------------

set -euo pipefail

# ── Colores ─────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() { echo -e "${BLUE}[INFO]${NC} $*"; }
print_ok()   { echo -e "${GREEN}[✓]${NC} $*"; }
print_warn() { echo -e "${YELLOW}[!]${NC} $*"; }
print_error(){ echo -e "${RED}[✗]${NC} $*"; }

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
    (docker compose build) &>/dev/null &
else
    (docker-compose build) &>/dev/null &
fi
spinner $!
wait $!
print_ok "Imágenes construidas."

# ── Paso 3 – Levantar los servicios ─────────────────────────────
print_step "Iniciando servicios..."
if docker compose version >/dev/null 2>&1; then
    (docker compose up -d) &>/dev/null &
else
    (docker-compose up -d) &>/dev/null &
fi
spinner $!
wait $!
print_ok "Servicios en marcha."

# ── Paso 4 – Esperar a que los contenedores estén listos ────────
print_step "Esperando a que los contenedores estén listos..."
sleep 5
print_ok "Listos."

# ── Paso 5 – Mostrar estado y puntos de acceso ───────────────────
echo
cat <<'EOF' | sed "s/^/$(printf \"${GREEN}\")/;s/$/$(printf \"${NC}\")/"
╔══════════════════════════════════════════════════════════╗
║                     ✅ Deploy finalizado                 ║
╚══════════════════════════════════════════════════════════╝
EOF

echo -e "${BLUE}Puntos de acceso:${NC}"
# Detectar IP pública (si se ejecuta en AWS)
if curl -s -m 5 http://169.254.169.254/latest/meta-data/public-ipv4 >/dev/null 2>&1; then
    PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
else
    PUBLIC_IP="localhost"
fi

if [[ "$PUBLIC_IP" == "localhost" ]]; then
    echo -e "  • Frontend: ${GREEN}http://localhost:3000${NC}"
    echo -e "  • Backend API: ${GREEN}http://localhost:8000${NC}"
else
    echo -e "  • Frontend: ${GREEN}http://${PUBLIC_IP}:3000${NC}"
    echo -e "  • Backend API: ${GREEN}http://${PUBLIC_IP}:8000${NC}"
    echo
    echo -e "${YELLOW}Puertos que deben estar abiertos en el firewall:${NC}"
    echo "  • TCP 3000  – Frontend"
    echo "  • TCP 8000  – API"
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
