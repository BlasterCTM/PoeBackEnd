#!/bin/bash

# Script de despliegue rápido a Azure
# Uso: ./deploy-azure.sh

set -e

echo "🚀 Iniciando despliegue de POE Backend a Azure..."

# Variables
RESOURCE_GROUP="rg-poe-proyecto"
ACR_NAME="poecr"
APP_NAME="poe-backend-api"
LOCATION="eastus"
IMAGE_NAME="poe-backend"
APP_PLAN="plan-poe-docker"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Login en Azure
echo -e "${YELLOW}📝 Login en Azure...${NC}"
az login

# 2. Crear ACR si no existe
echo -e "${YELLOW}🐳 Creando Azure Container Registry...${NC}"
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --location $LOCATION \
  --admin-enabled true || echo "ACR ya existe"

# 3. Login en ACR
echo -e "${YELLOW}🔐 Login en ACR...${NC}"
az acr login --name $ACR_NAME

# 4. Construir imagen en ACR
echo -e "${YELLOW}🔨 Construyendo imagen en ACR...${NC}"
az acr build \
  --registry $ACR_NAME \
  --image $IMAGE_NAME:latest \
  --file docker/Dockerfile \
  .

# 5. Crear App Service Plan si no existe
echo -e "${YELLOW}📋 Creando App Service Plan...${NC}"
az appservice plan create \
  --name $APP_PLAN \
  --resource-group $RESOURCE_GROUP \
  --is-linux \
  --sku B1 \
  --location $LOCATION || echo "Plan ya existe"

# 6. Crear Web App si no existe
echo -e "${YELLOW}🌐 Creando Web App...${NC}"
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_PLAN \
  --name $APP_NAME \
  --deployment-container-image-name $ACR_NAME.azurecr.io/$IMAGE_NAME:latest || echo "Web App ya existe"

# 7. Obtener credenciales de ACR
echo -e "${YELLOW}🔑 Configurando credenciales...${NC}"
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

# 8. Configurar contenedor en Web App
echo -e "${YELLOW}⚙️  Configurando contenedor...${NC}"
az webapp config container set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --docker-custom-image-name $ACR_NAME.azurecr.io/$IMAGE_NAME:latest \
  --docker-registry-server-url https://$ACR_NAME.azurecr.io \
  --docker-registry-server-user $ACR_USERNAME \
  --docker-registry-server-password $ACR_PASSWORD

# 9. Configurar variables de entorno
echo -e "${YELLOW}🔧 Configurando variables de entorno...${NC}"
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --settings \
    DATABASE_TARGET=azure \
    AZURE_POSTGRES_HOST=rg-poe-proyecto.postgres.database.azure.com \
    AZURE_POSTGRES_PORT=5432 \
    AZURE_POSTGRES_USER=admin_blast \
    AZURE_POSTGRES_DB=POE \
    ACCESS_TOKEN_EXPIRE_MINUTES=60 \
    REFRESH_TOKEN_EXPIRE_DAYS=60 \
    MAX_TAREAS_PENDIENTES_POR_REPONEDOR=5 \
    SUPERADMIN_EMAIL=admin@poe.com \
    SUPERADMIN_NAME="Administrador Principal" \
    WEBSITES_PORT=8000

# Nota: Configurar secretos manualmente por seguridad
echo -e "${YELLOW}⚠️  IMPORTANTE: Configurar manualmente en Azure Portal:${NC}"
echo "  - AZURE_POSTGRES_PASSWORD"
echo "  - SECRET_KEY"
echo "  - REFRESH_SECRET_KEY"
echo "  - SUPERADMIN_PASSWORD (password inicial del superadmin)"

# 10. Habilitar logging
echo -e "${YELLOW}📊 Habilitando logs...${NC}"
az webapp log config \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --docker-container-logging filesystem

# 11. Habilitar continuous deployment
echo -e "${YELLOW}🔄 Habilitando continuous deployment...${NC}"
az webapp deployment container config \
  --enable-cd true \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP

# 12. Reiniciar app
echo -e "${YELLOW}🔄 Reiniciando aplicación...${NC}"
az webapp restart \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP

echo -e "${GREEN}✅ ¡Despliegue completado!${NC}"
echo ""
echo "📍 URL de tu API: https://$APP_NAME.azurewebsites.net"
echo "📚 Documentación: https://$APP_NAME.azurewebsites.net/docs"
echo ""
echo "Ver logs:"
echo "  az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
