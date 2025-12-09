# 🐳 Docker Configuration

Esta carpeta contiene todos los archivos relacionados con Docker para el proyecto POE Backend.

## 📁 Archivos

- **`Dockerfile`** - Imagen Docker de producción con Python 3.11 + Gunicorn
- **`docker-compose.yml`** - Orquestación de contenedores para desarrollo local
- **`.dockerignore`** - Archivos excluidos de la imagen Docker

## 🚀 Uso Rápido

### Construcción Local

```bash
# Desde la raíz del proyecto
docker build -f docker/Dockerfile -t poe-backend:latest .
```

### Ejecución Local

```bash
# Con variables de entorno del archivo .env
docker run -p 8000:8000 --env-file .env poe-backend:latest

# Probar API
curl http://localhost:8000/docs
```

### Con Docker Compose

```bash
# Desde la raíz del proyecto
docker-compose -f docker/docker-compose.yml up --build

# Detener
docker-compose -f docker/docker-compose.yml down
```

## 📝 Notas

- El `Dockerfile` está optimizado para producción con multi-stage build
- Las variables de entorno se leen del archivo `.env` o se configuran en Azure
- El puerto expuesto es `8000`
- Se utiliza Gunicorn con workers de Uvicorn para mejor rendimiento
