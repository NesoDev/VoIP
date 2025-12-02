# Deployment en AWS Lightsail

## Configuración Especial para Lightsail

En AWS Lightsail, los clientes vienen de **Internet público**, no de LAN local. Por eso la configuración NAT es diferente.

### Cambios necesarios en `pjsip.conf.tpl`

**Para LAN local (desarrollo):**
```ini
; local_net=192.168.0.0/16  ← COMENTADO
external_media_address=EXTERNAL_IP_PLACEHOLDER
external_signaling_address=EXTERNAL_IP_PLACEHOLDER
```

**Para AWS Lightsail (producción):**
```ini
local_net=192.168.0.0/16  ← DESCOMENTADO
local_net=172.16.0.0/12
local_net=10.0.0.0/8
external_media_address=EXTERNAL_IP_PLACEHOLDER
external_signaling_address=EXTERNAL_IP_PLACEHOLDER
```

### Por qué es diferente

- **Local:** Los teléfonos están en tu red WiFi (192.168.x.x). Si `local_net=192.168` está activo, Asterisk piensa que son "locales" y les envía su IP de Docker (172.x), causando fallo de audio.

- **Lightsail:** Los teléfonos vienen de internet (IPs públicas). Con `local_net=192.168` activo, Asterisk correctamente los trata como "externos" y les envía la IP pública de la instancia.

### Solución Automática

Actualiza tu `start.sh` para detectar el entorno:

```bash
# Detectar si estamos en AWS
if curl -s -m 2 http://169.254.169.254/latest/meta-data/public-ipv4 > /dev/null 2>&1; then
    echo "Entorno: AWS"
    IS_AWS=true
    PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
else
    echo "Entorno: Local"
    IS_AWS=false
    DETECTED_IP=$(ipconfig getifaddr en0 2>/dev/null || hostname -I | awk '{print $1}' 2>/dev/null)
    PUBLIC_IP="$DETECTED_IP"
fi

export PUBLIC_IP

# Generar pjsip.conf con configuración NAT apropiada
if [ "$IS_AWS" = true ]; then
    # AWS: Habilitar local_net
    sed "s/EXTERNAL_IP_PLACEHOLDER/$PUBLIC_IP/g; s/^; local_net=192.168/local_net=192.168/" asterisk/pjsip.conf.tpl > asterisk/pjsip.conf
else
    # Local: Mantener local_net comentado
    sed "s/EXTERNAL_IP_PLACEHOLDER/$PUBLIC_IP/g" asterisk/pjsip.conf.tpl > asterisk/pjsip.conf
fi
```

### Puertos a abrir en Lightsail

```
TCP  3000         - Web UI
UDP  5060         - SIP Signaling
UDP  10000-10100 - RTP (Audio)
```

### Verificación

Después de desplegar en Lightsail:

```bash
# SSH a la instancia
ssh ubuntu@YOUR_IP

# Ver endpoints registrados
docker exec voip-asterisk asterisk -rx "pjsip show endpoints"

# Ver configuración NAT
docker exec voip-asterisk asterisk -rx "pjsip show transports"
```
