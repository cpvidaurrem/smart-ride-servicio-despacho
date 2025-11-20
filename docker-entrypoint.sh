#!/bin/bash
set -e

echo "🚀 Iniciando Servicio de Despacho..."

# Esperar PostgreSQL
echo "⏳ Esperando PostgreSQL..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
    sleep 2
done
echo "✅ PostgreSQL listo"

# ✅ Generar archivos proto en src/generated
echo "🔧 Generando archivos proto desde /app/proto..."

mkdir -p /app/src/generated
touch /app/src/generated/__init__.py

python -m grpc_tools.protoc \
  -I/app/proto \
  --python_out=/app/src/generated \
  --grpc_python_out=/app/src/generated \
  /app/proto/reservas.proto

if [ $? -eq 0 ]; then
    echo "✅ Proto files generados en /app/src/generated/"
    ls -la /app/src/generated/
    
    # ✅ NUEVO: Verificar que los archivos se generaron
    if [ -f "/app/src/generated/reservas_pb2.py" ]; then
        echo "✅ reservas_pb2.py generado correctamente"
    else
        echo "❌ ERROR: reservas_pb2.py NO fue generado"
        exit 1
    fi
    
    if [ -f "/app/src/generated/reservas_pb2_grpc.py" ]; then
        echo "✅ reservas_pb2_grpc.py generado correctamente"
    else
        echo "❌ ERROR: reservas_pb2_grpc.py NO fue generado"
        exit 1
    fi
else
    echo "❌ Error generando proto files"
    exit 1
fi

# ✅ NUEVO: Añadir /app/src/generated al PYTHONPATH
export PYTHONPATH="/app/src/generated:$PYTHONPATH"
echo "✅ PYTHONPATH actualizado: $PYTHONPATH"

# Iniciar API
echo "🌐 Iniciando API FastAPI en puerto $PORT..."
exec uvicorn src.main:app --host 0.0.0.0 --port $PORT --log-level info