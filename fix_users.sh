#!/bin/bash
# Script para limpiar las secciones [identifyXXX] problemáticas

echo "Limpiando configuración de usuarios..."

# Backup
cp asterisk/pjsip_custom.conf asterisk/pjsip_custom.conf.bak

# Eliminar todas las secciones [identifyXXX]
sed -i '' '/^\[identify[0-9]*\]/,/^match=/d' asterisk/pjsip_custom.conf

echo "✓ Secciones [identify] eliminadas"
echo "✓ Backup guardado en pjsip_custom.conf.bak"
echo ""
echo "Ahora ejecuta: docker compose restart asterisk"
