#!/bin/bash
# Script para configurar variables de entorno en Azure App Service
# Ejecutar: ./configure-azure-env.sh

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}CONFIGURAR VARIABLES DE ENTORNO - AZURE${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Variables de configuración
read -p "Nombre del App Service (ej: poe-backend-api): " APP_NAME
read -p "Nombre del Resource Group (default: rg-poe-proyecto): " RESOURCE_GROUP
RESOURCE_GROUP=${RESOURCE_GROUP:-rg-poe-proyecto}

echo -e "\n${YELLOW}Configurando base de datos PostgreSQL...${NC}"
read -p "PostgreSQL Host (default: rg-poe-proyecto.postgres.database.azure.com): " POSTGRES_HOST
POSTGRES_HOST=${POSTGRES_HOST:-rg-poe-proyecto.postgres.database.azure.com}

read -p "PostgreSQL User (default: admin_blast): " POSTGRES_USER
POSTGRES_USER=${POSTGRES_USER:-admin_blast}

read -sp "PostgreSQL Password: " POSTGRES_PASSWORD
echo ""

read -p "PostgreSQL Database (default: POE): " POSTGRES_DB
POSTGRES_DB=${POSTGRES_DB:-POE}

echo -e "\n${YELLOW}Configurando seguridad...${NC}"
read -sp "SECRET_KEY (generada anteriormente): " SECRET_KEY
echo ""

read -sp "REFRESH_SECRET_KEY (generada anteriormente): " REFRESH_SECRET_KEY
echo ""

echo -e "\n${YELLOW}Configurando SuperAdmin...${NC}"
read -p "SuperAdmin Email (default: superadmin@poe.com): " SUPERADMIN_EMAIL
SUPERADMIN_EMAIL=${SUPERADMIN_EMAIL:-superadmin@poe.com}

read -sp "SuperAdmin Password: " SUPERADMIN_PASSWORD
echo ""

read -p "SuperAdmin Name (default: Super Administrador): " SUPERADMIN_NAME
SUPERADMIN_NAME=${SUPERADMIN_NAME:-"Super Administrador"}

echo -e "\n${YELLOW}Configurando CORS...${NC}"
read -p "CORS Origins (ej: https://frontend.com,https://app.com): " CORS_ORIGINS

echo -e "\n${GREEN}Aplicando configuración a Azure App Service...${NC}\n"

az webapp config appsettings set \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --settings \
    DATABASE_TARGET=azure \
    AZURE_POSTGRES_HOST="$POSTGRES_HOST" \
    AZURE_POSTGRES_PORT=5432 \
    AZURE_POSTGRES_USER="$POSTGRES_USER" \
    AZURE_POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
    AZURE_POSTGRES_DB="$POSTGRES_DB" \
    SECRET_KEY="$SECRET_KEY" \
    REFRESH_SECRET_KEY="$REFRESH_SECRET_KEY" \
    SUPERADMIN_EMAIL="$SUPERADMIN_EMAIL" \
    SUPERADMIN_PASSWORD="$SUPERADMIN_PASSWORD" \
    SUPERADMIN_NAME="$SUPERADMIN_NAME" \
    ENVIRONMENT=production \
    DEBUG=False \
    CORS_ORIGINS="$CORS_ORIGINS" \
    LOG_LEVEL=INFO \
    ACCESS_TOKEN_EXPIRE_MINUTES=30 \
    REFRESH_TOKEN_EXPIRE_MINUTES=10080 \
    API_V1_PREFIX=/api/v1 \
    PROJECT_NAME="POE - Path Optimization Engine" \
    VERSION=1.0.0

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ Variables de entorno configuradas exitosamente${NC}\n"
    
    echo -e "${YELLOW}Configurando regla de firewall PostgreSQL...${NC}"
    az postgres flexible-server firewall-rule create \
      --resource-group "$RESOURCE_GROUP" \
      --name "$POSTGRES_HOST" \
      --rule-name AllowAzureServices \
      --start-ip-address 0.0.0.0 \
      --end-ip-address 0.0.0.0 2>/dev/null || echo "Regla ya existe"
    
    echo -e "\n${GREEN}✅ Configuración completada${NC}"
    echo -e "\n${YELLOW}Próximos pasos:${NC}"
    echo "1. Reiniciar App Service: az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP"
    echo "2. Ver logs: az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
    echo "3. Verificar health: curl https://$APP_NAME.azurewebsites.net/health"
else
    echo -e "\n${RED}❌ Error al configurar variables de entorno${NC}\n"
    exit 1
fi
