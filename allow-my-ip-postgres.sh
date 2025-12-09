#!/bin/bash
# Script para agregar tu IP pública al firewall de PostgreSQL Azure
# Ejecutar: ./allow-my-ip-postgres.sh

set -e

echo "🔍 Obteniendo tu IP pública..."
MY_IP=$(curl -s https://api.ipify.org)

echo "📍 Tu IP pública es: $MY_IP"
echo ""

read -p "Nombre del servidor PostgreSQL (default: rg-poe-proyecto): " SERVER_NAME
SERVER_NAME=${SERVER_NAME:-rg-poe-proyecto}

read -p "Resource Group (default: rg-poe-proyecto): " RESOURCE_GROUP
RESOURCE_GROUP=${RESOURCE_GROUP:-rg-poe-proyecto}

echo ""
echo "🔧 Agregando regla de firewall para tu IP..."

az postgres flexible-server firewall-rule create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$SERVER_NAME" \
  --rule-name "AllowMyIP-$(date +%Y%m%d)" \
  --start-ip-address "$MY_IP" \
  --end-ip-address "$MY_IP"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Firewall configurado exitosamente"
    echo "📍 Tu IP $MY_IP ahora puede conectarse a PostgreSQL Azure"
    echo ""
    echo "🐳 Ahora puedes ejecutar:"
    echo "   docker run --name poe-backend-test --env-file .env -p 8000:8000 poe-backend:local"
else
    echo ""
    echo "❌ Error al configurar firewall"
    echo "Verifica que estés logueado en Azure CLI: az login"
fi
