FROM python:3.12-slim AS base

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Instalar dependencias del sistema + curl
RUN apt-get update && apt-get install -y \
    postgresql-client \
    netcat-openbsd \
    dos2unix \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY src/ src/

#  Crear directorio para proto generados
RUN mkdir -p /app/src/generated && \
    touch /app/src/generated/__init__.py

# Crear usuario no-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Exponer puerto
EXPOSE 8003

# Script de inicio
COPY --chown=appuser:appuser docker-entrypoint.sh /app/
RUN dos2unix /app/docker-entrypoint.sh && chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]