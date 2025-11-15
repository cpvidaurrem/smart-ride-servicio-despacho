#!/bin/bash
set -e

echo "🚀 Iniciando Servicio de Despacho..."

# Esperar PostgreSQL con sintaxis CORRECTA
echo "⏳ Esperando PostgreSQL..."
until PGPASSWORD=password pg_isready -h postgres-despacho -p 5432 -U usuario -d db_smartride_despacho 2>/dev/null; do
  echo "PostgreSQL no disponible, esperando..."
  sleep 2
done
echo "✅ PostgreSQL está listo"

# Esperar RabbitMQ usando Python
echo "⏳ Esperando RabbitMQ..."
until python3 -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('rabbitmq-despacho', 5672)); s.close()" 2>/dev/null; do
  echo "RabbitMQ no disponible, esperando..."
  sleep 2
done
echo "✅ RabbitMQ está listo"

# Determinar qué servicio iniciar
if [ "$1" = "grpc" ]; then
    echo "🌐 Iniciando servidor gRPC..."
    exec python -m src.grpc.server
else
    echo "🌐 Iniciando API FastAPI..."
    exec uvicorn src.main:app --host 0.0.0.0 --port 8003
fi