#!/usr/bin/env bash
# ------------------------------------------------------------
#  setup.sh – Prepara el entorno (Docker, Docker‑Compose, .env)
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
║                VoIP Demo – Preparación del Entorno      ║
╚══════════════════════════════════════════════════════════╝
EOF
echo

# ── Paso 1 – Detectar entorno (AWS vs local) ─────────────────────
print_step "Detectando entorno..."
if curl -s -m 5 http://169.254.169.254/latest/meta-data/public-ipv4 >/dev/null 2>&1; then
    PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
    print_ok "AWS detectado – IP pública: $PUBLIC_IP"
else
    PUBLIC_IP="localhost"
    print_ok "Entorno local detectado"
fi

# ── Paso 2 – Verificar Docker y Docker‑Compose ─────────────────────
print_step "Comprobando Docker..."
DOCKER_MISSING=false
COMPOSE_MISSING=false

if ! command -v docker >/dev/null 2>&1; then
    print_warn "Docker no encontrado"
    DOCKER_MISSING=true
else
    print_ok "Docker $(docker --version | awk '{print $3}' | sed 's/,//')"
fi

if docker compose version >/dev/null 2>&1; then
    print_ok "Docker‑Compose $(docker compose version --short)"
elif command -v docker-compose >/dev/null 2>&1; then
    print_ok "Docker‑Compose $(docker-compose --version | awk '{print $3}' | sed 's/,//')"
else
    print_warn "Docker‑Compose no encontrado"
    COMPOSE_MISSING=true
fi

# ── Paso 3 – Instalar componentes faltantes ─────────────────────
if $DOCKER_MISSING || $COMPOSE_MISSING; then
    echo
    print_warn "Componentes faltantes detectados"
    read -p "$(printf \"${YELLOW}Instalar los componentes faltantes? [y/N]: ${NC}\")" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # ---- Docker -------------------------------------------------
        if $DOCKER_MISSING; then
            print_step "Instalando Docker..."
            (
                sudo apt-get update -qq &&
                sudo apt-get install -y -qq ca-certificates curl gnupg lsb-release &&
                sudo mkdir -p /etc/apt/keyrings &&
                curl -fsSL https://download.docker.com/linux/ubuntu/gpg |
                    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg &&
                echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
                      https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" |
                    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null &&
                sudo apt-get update -qq &&
                sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io \
                    docker-buildx-plugin docker-compose-plugin
            ) &>/dev/null &
            spinner $!
            wait $!
            sudo usermod -aG docker "$USER"
            print_ok "Docker instalado"
            print_warn "Necesitas cerrar sesión y volver a entrar para que el grupo docker surta efecto"
        fi
        # ---- Docker‑Compose (solo si Docker ya estaba) -------------
        if $COMPOSE_MISSING && ! $DOCKER_MISSING; then
            print_step "Instalando Docker‑Compose (standalone)..."
            (
                sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
                    -o /usr/local/bin/docker-compose &&
                sudo chmod +x /usr/local/bin/docker-compose
            ) &>/dev/null &
            spinner $!
            wait $!
            print_ok "Docker‑Compose instalado"
        fi
    else
        print_error "Instalación cancelada. Instala Docker y Docker‑Compose manualmente y vuelve a ejecutar setup.sh."
        exit 1
    fi
fi

# ── Paso 4 – Generar .env para el frontend ───────────────────────
print_step "Generando archivo .env..."
mkdir -p frontend
cat > frontend/.env <<EOF
API_BASE=http://${PUBLIC_IP}:8000
WS_BASE=ws://${PUBLIC_IP}:8000
EOF
print_ok ".env creado"

# ── Paso 5 – Resumen final ─────────────────────────────────────
echo
cat <<'EOF' | sed "s/^/$(printf \"${GREEN}\")/;s/$/$(printf \"${NC}\")/"
╔══════════════════════════════════════════════════════════╗
║                ✅ Preparación completada                ║
╚══════════════════════════════════════════════════════════╝
EOF

echo -e "${BLUE}Ejecuta ${GREEN}./start.sh${BLUE} para lanzar los contenedores.${NC}"
