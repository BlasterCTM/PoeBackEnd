#!/bin/bash
set -e

echo "🚀 Iniciando POE Backend en Azure..."

# Esperar a que PostgreSQL esté disponible
echo "⏳ Esperando a que PostgreSQL esté disponible..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if python -c "from app.core.database.database import engine; engine.connect()" 2>/dev/null; then
        echo "✅ Conexión a PostgreSQL establecida"
        break
    fi
    
    echo "⏳ Intento $attempt de $max_attempts - esperando PostgreSQL..."
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ No se pudo conectar a PostgreSQL después de $max_attempts intentos"
    exit 1
fi

# Ejecutar inicialización de base de datos
echo "📋 Ejecutando inicialización de base de datos..."
python init_db.py

if [ $? -ne 0 ]; then
    echo "❌ Error en la inicialización de la base de datos"
    exit 1
fi

# Iniciar servidor con Gunicorn
echo "🚀 Iniciando servidor FastAPI con Gunicorn..."
exec gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
