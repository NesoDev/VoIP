#!/bin/bash
echo "=== Diagnóstico de Audio VoIP ==="
echo ""
echo "1. Verificando puertos RTP expuestos..."
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep voip-asterisk
echo ""
echo "2. Habilitando debug RTP en Asterisk..."
docker exec voip-asterisk asterisk -rx "rtp set debug on"
docker exec voip-asterisk asterisk -rx "pjsip set logger on"
echo ""
echo "3. Mostrando configuración NAT actual..."
docker exec voip-asterisk asterisk -rx "pjsip show transports"
echo ""
echo "=== Ahora haz una llamada y verás el tráfico RTP ==="
echo "Presiona Ctrl+C cuando termines."
echo ""
docker compose logs -f asterisk
