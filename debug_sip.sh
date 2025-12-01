#!/bin/bash
echo "Habilitando logs SIP en Asterisk..."
docker exec voip-asterisk asterisk -rx "pjsip set logger on"
echo "Logs habilitados. Mostrando tráfico SIP en tiempo real (Ctrl+C para salir)..."
echo "--------------------------------------------------------------------------------"
docker compose logs -f asterisk
