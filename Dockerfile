# Etapa Base
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Etapa gRPC Builder
FROM base AS grpc-builder

COPY src/grpc/despacho.proto src/grpc/

# Generar archivos gRPC
RUN python -m grpc_tools.protoc \
    -I. \
    --python_out=. \
    --grpc_python_out=. \
    src/grpc/despacho.proto

# Etapa Producción (API FastAPI)
FROM base AS production

# Copiar código fuente
COPY src/ src/
COPY migrations/ migrations/

# Copiar archivos generados de gRPC
COPY --from=grpc-builder /app/src/grpc/despacho_pb2.py src/grpc/
COPY --from=grpc-builder /app/src/grpc/despacho_pb2_grpc.py src/grpc/

# Crear usuario no-root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Copiar script de entrada
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

USER appuser

EXPOSE 8003

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["api"]

# Etapa gRPC Server
FROM production AS grpc

EXPOSE 50051

CMD ["grpc"]