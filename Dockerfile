# Etapa 1: Base con Python
FROM python:3.11-slim as base

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Etapa 2: Generar archivos gRPC
FROM base as grpc-builder

# Copiar archivo proto
COPY src/grpc/despacho.proto src/grpc/

# Generar archivos gRPC
RUN python -m grpc_tools.protoc \
    -I. \
    --python_out=. \
    --grpc_python_out=. \
    src/grpc/despacho.proto

# Etapa 3: Producción
FROM base as production

# Copiar código fuente
COPY src/ src/
COPY migrations/ migrations/

# Copiar archivos generados de gRPC desde builder
COPY --from=grpc-builder /app/src/grpc/despacho_pb2.py src/grpc/
COPY --from=grpc-builder /app/src/grpc/despacho_pb2_grpc.py src/grpc/

# Crear usuario no-root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Exponer puertos
EXPOSE 8003 50051

# Script de inicio
COPY --chown=appuser:appuser docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["api"]