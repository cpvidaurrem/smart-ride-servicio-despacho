#!/bin/bash
set -e

echo "🚀 Iniciando Servicio de Despacho..."

# Esperar a que PostgreSQL esté disponible
echo "⏳ Esperando PostgreSQL..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
    sleep 2
done
echo "✅ PostgreSQL está listo"

# Iniciar API
echo "🌐 Iniciando API FastAPI..."
exec uvicorn src.main:app --host 0.0.0.0 --port $PORT