#!/bin/bash
set -e

echo "🚀 Iniciando Servicio de Despacho..."

# Esperar a que PostgreSQL esté disponible
echo "⏳ Esperando PostgreSQL..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
    echo "PostgreSQL no disponible, esperando..."
    sleep 2
done
echo "✅ PostgreSQL está listo"

# Esperar a que RabbitMQ esté disponible
echo "⏳ Esperando RabbitMQ..."
while ! nc -z $RABBITMQ_HOST $RABBITMQ_PORT; do
    echo "RabbitMQ no disponible, esperando..."
    sleep 2
done
echo "✅ RabbitMQ está listo"

# Ejecutar según el comando
case "$1" in
    api)
        echo "🌐 Iniciando API FastAPI..."
        exec uvicorn src.main:app --host 0.0.0.0 --port $PORT
        ;;
    grpc)
        echo "📡 Iniciando servidor gRPC..."
        exec python -m src.grpc.server
        ;;
    consumer)
        echo "📨 Iniciando consumidor RabbitMQ..."
        exec python -m src.messaging.rabbitmq_consumer
        ;;
    *)
        echo "Comando no reconocido: $1"
        echo "Opciones: api, grpc, consumer"
        exit 1
        ;;
esac