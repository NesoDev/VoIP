FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libportaudio2 \
    libportaudiocpp0 \
    portaudio19-dev \
    pkg-config \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    libavdevice-dev \
    libavfilter-dev \
    libavresample-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Exponer puertos
# 8000: API FastAPI
# 5060: SIP (UDP)
# 10000-10100: RTP (UDP)
EXPOSE 8000 5060/udp 10000-10100/udp

# Comando de inicio
CMD ["python", "main.py"]
