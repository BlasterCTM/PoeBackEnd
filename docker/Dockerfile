FROM python:3.11-slim

# Configurar variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para psycopg y otros
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY ./app ./app
COPY ./init_db.py ./init_db.py
COPY ./docker/startup.sh ./startup.sh

# Dar permisos de ejecución al script de startup
RUN chmod +x ./startup.sh

# Exponer el puerto
EXPOSE 8000

# Comando de inicio con script que inicializa DB
CMD ["./startup.sh"]
