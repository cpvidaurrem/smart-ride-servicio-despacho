# 🚀 Guía de Ejecución Paso a Paso - Servicio de Despacho

## 📋 Pre-requisitos

Asegúrate de tener instalado:
- Docker y Docker Compose
- Git
- Python 3.11+ (para desarrollo local)
- PostgreSQL (para desarrollo local)
- RabbitMQ (para desarrollo local)

## 🐳 Opción 1: Ejecución con Docker (RECOMENDADO)

### Paso 1: Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/smart-ride-servicio-despacho.git
cd smart-ride-servicio-despacho
```

### Paso 2: Crear archivo .env

```bash
cp .env.example .env
```

Editar `.env` con tus configuraciones (puedes dejar los valores por defecto para testing):

```env
# Variables básicas
APP_NAME="Servicio de Despacho - Smart Ride"
ENVIRONMENT=development
DEBUG=True
PORT=8003

# Base de datos
DB_NAME=despacho_db
DB_USER=despacho_user
DB_PASSWORD=despacho_pass
DB_PORT=5432

# RabbitMQ
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_PORT=5672

# gRPC
GRPC_PORT=50051
```

### Paso 3: Generar archivos gRPC (antes del build)

```bash
# Instalar grpcio-tools temporalmente
pip install grpcio-tools

# Generar archivos proto
python -m grpc_tools.protoc \
    -I. \
    --python_out=. \
    --grpc_python_out=. \
    src/grpc/despacho.proto
```

### Paso 4: Construir las imágenes Docker

```bash
docker-compose build
```

### Paso 5: Iniciar los servicios

```bash
docker-compose up
```

O en modo detached (segundo plano):
```bash
docker-compose up -d
```

### Paso 6: Verificar que todo está corriendo

```bash
# Ver logs
docker-compose logs -f

# Verificar contenedores activos
docker-compose ps

# Health check de la API
curl http://localhost:8003/health
```

**Salida esperada:**
```json
{
  "status": "healthy",
  "servicio": "Servicio de Despacho - Smart Ride",
  "version": "1.0.0",
  "rabbitmq": "connected"
}
```

### Paso 7: Acceder a las interfaces

- **API REST**: http://localhost:8003
- **Swagger Documentation**: http://localhost:8003/docs
- **ReDoc**: http://localhost:8003/redoc
- **RabbitMQ Management**: http://localhost:15672 (usuario: guest, contraseña: guest)

### Paso 8: Probar el servicio

#### a) Listar conductores de prueba:
```bash
curl http://localhost:8003/api/v1/conductores/
```

#### b) Crear un nuevo conductor:
```bash
curl -X POST http://localhost:8003/api/v1/conductores/ \
  -H "Content-Type: application/json" \
  -d '{
    "id_usuario": 201,
    "nombre_completo": "Carlos Mendoza",
    "licencia": "LIC-98765",
    "modelo_auto": "Nissan Versa 2022",
    "placa_auto": "XYZ-4321"
  }'
```

#### c) Cambiar estado a disponible:
```bash
# Reemplaza {id} con el ID del conductor
curl -X PATCH http://localhost:8003/api/v1/conductores/6/estado \
  -H "Content-Type: application/json" \
  -d '{"estado": "disponible"}'
```

#### d) Ver conductores disponibles:
```bash
curl http://localhost:8003/api/v1/conductores/disponibles
```

#### e) Crear asignación automática:
```bash
curl -X POST "http://localhost:8003/api/v1/asignaciones/automatica?algoritmo=round_robin" \
  -H "Content-Type: application/json" \
  -d '{
    "id_viaje": 1001,
    "id_pasajero": 500,
    "origen": "Plaza 25 de Mayo",
    "destino": "Terminal de Buses",
    "prioridad": 1
  }'
```

#### f) Ver estadísticas:
```bash
curl http://localhost:8003/api/v1/asignaciones/stats
```

### Paso 9: Probar integración con RabbitMQ

Crear un script Python `test_rabbitmq.py`:

```python
import pika
import json
import time

# Conectar a RabbitMQ
connection = pika.BlockingConnection(
    pika.ConnectionParameters('localhost')
)
channel = connection.channel()

# Crear mensaje de nueva reserva
mensaje = {
    "id_viaje": 2001,
    "id_pasajero": 600,
    "origen": "Aeropuerto",
    "destino": "Centro",
    "prioridad": 1,
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
}

print(f"📤 Enviando mensaje: {mensaje}")

# Publicar en el exchange
channel.basic_publish(
    exchange='smart_ride_exchange',
    routing_key='reserva.nueva',
    body=json.dumps(mensaje)
)

print("✅ Mensaje enviado!")
connection.close()
```

Ejecutar:
```bash
python test_rabbitmq.py
```

Luego verificar en los logs que se procesó:
```bash
docker-compose logs despacho-api | grep "Mensaje recibido"
```

### Paso 10: Detener los servicios

```bash
# Detener sin eliminar volúmenes
docker-compose down

# Detener y eliminar volúmenes (limpieza completa)
docker-compose down -v
```

---

## 💻 Opción 2: Ejecución Local (Sin Docker)

### Paso 1: Clonar y preparar entorno

```bash
git clone https://github.com/tu-usuario/smart-ride-servicio-despacho.git
cd smart-ride-servicio-despacho

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows
```

### Paso 2: Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 3: Configurar PostgreSQL

```bash
# Crear base de datos
createdb despacho_db

# O con psql
psql -U postgres
CREATE DATABASE despacho_db;
CREATE USER despacho_user WITH PASSWORD 'despacho_pass';
GRANT ALL PRIVILEGES ON DATABASE despacho_db TO despacho_user;
\q

# Ejecutar script de inicialización
psql -U despacho_user -d despacho_db -f migrations/init.sql
```

### Paso 4: Instalar y configurar RabbitMQ

#### Ubuntu/Debian:
```bash
sudo apt-get install rabbitmq-server
sudo systemctl start rabbitmq-server
sudo rabbitmq-plugins enable rabbitmq_management
```

#### Mac:
```bash
brew install rabbitmq
brew services start rabbitmq
```

#### Windows:
Descargar desde: https://www.rabbitmq.com/download.html

### Paso 5: Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env`:
```env
DATABASE_URL=postgresql://despacho_user:despacho_pass@localhost:5432/despacho_db
DB_HOST=localhost
RABBITMQ_HOST=localhost
REDIS_HOST=localhost
```

### Paso 6: Generar archivos gRPC

```bash
python -m grpc_tools.protoc \
    -I. \
    --python_out=. \
    --grpc_python_out=. \
    src/grpc/despacho.proto
```

### Paso 7: Iniciar servicios

#### Terminal 1 - API REST:
```bash
python -m uvicorn src.main:app --reload --port 8003
```

#### Terminal 2 - Servidor gRPC:
```bash
python -m src.grpc.server
```

#### Terminal 3 - Consumidor RabbitMQ (Opcional):
```bash
python -m src.messaging.rabbitmq_consumer
```

### Paso 8: Verificar

```bash
curl http://localhost:8003/health
```

---

## 🧪 Ejecutar Tests

```bash
# Con el entorno virtual activado
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=src --cov-report=html
```

---

## 🔧 Troubleshooting

### Error: Puerto 8003 ya en uso

```bash
# Linux/Mac
lsof -ti:8003 | xargs kill -9

# Windows
netstat -ano | findstr :8003
taskkill /PID <PID> /F
```

### Error: No se puede conectar a PostgreSQL

```bash
# Verificar que PostgreSQL está corriendo
sudo systemctl status postgresql

# Reiniciar
sudo systemctl restart postgresql
```

### Error: RabbitMQ no responde

```bash
# Ver logs
docker-compose logs rabbitmq

# Reiniciar solo RabbitMQ
docker-compose restart rabbitmq
```

### Error: No se generan archivos gRPC

```bash
# Instalar herramientas gRPC
pip install grpcio-tools

# Regenerar
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. src/grpc/despacho.proto
```

### Base de datos no se inicializa

```bash
# Eliminar volúmenes y recrear
docker-compose down -v
docker-compose up --build
```

---

## 📊 Monitoreo en Producción

```bash
# Ver logs en tiempo real
docker-compose logs -f despacho-api

# Ver logs del consumidor
docker-compose logs -f despacho-consumer

# Ver logs de RabbitMQ
docker-compose logs -f rabbitmq

# Ver uso de recursos
docker stats
```

---

## 🎯 Siguientes Pasos

1. ✅ Servicio corriendo
2. ✅ Tests básicos pasando
3. 📝 Integrar con Servicio de Reservas (gRPC)
4. 📝 Configurar Nginx como proxy inverso
5. 📝 Implementar monitoreo con Prometheus/Grafana
6. 📝 Pruebas de carga con JMeter
7. 📝 Deploy en staging/producción

---

## 📞 Soporte

Si tienes problemas, revisa:
- Logs de Docker: `docker-compose logs`
- Documentación Swagger: http://localhost:8003/docs
- RabbitMQ Management: http://localhost:15672

**Contacto:**
- kristian2vidaurre@gmail.com
- Universidad San Francisco Xavier de Chuquisaca