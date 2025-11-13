# 🚕 Servicio de Despacho - Smart Ride

Microservicio de asignación automática de conductores desarrollado con **Python + FastAPI + gRPC + RabbitMQ** - **Totalmente Dockerizado**.

## 📋 Descripción

El Servicio de Despacho es responsable de:
- Recibir solicitudes de viaje desde el Servicio de Reservas (vía RabbitMQ)
- Asignar conductores disponibles usando algoritmos inteligentes
- Comunicar las asignaciones mediante gRPC y eventos RabbitMQ
- Gestionar el estado y disponibilidad de conductores
- Soportar alta concurrencia de solicitudes

## 🛠️ Tecnologías

- **Lenguaje**: Python 3.11+
- **Framework**: FastAPI
- **Base de Datos**: PostgreSQL
- **Mensajería**: RabbitMQ (pika)
- **RPC**: gRPC
- **Caché**: Redis
- **Contenedores**: Docker + Docker Compose
- **ORM**: SQLAlchemy
- **Validación**: Pydantic

## 🚀 Ejecución con Docker

### Paso 1: Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/smart-ride-servicio-despacho.git
cd smart-ride-servicio-despacho
```

### Paso 2: Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env si necesitas personalizar (opcional)
```

### Paso 3: Construir e iniciar servicios

```bash
docker-compose up --build
```

### Paso 4: Verificar que todo está corriendo

```bash
# Health check
curl http://localhost:8003/health

# Ver logs
docker-compose logs -f

# Ver contenedores activos
docker-compose ps
```

### Paso 5: Acceder a las interfaces

- **API REST**: http://localhost:8003
- **Swagger Documentation**: http://localhost:8003/docs
- **ReDoc**: http://localhost:8003/redoc
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

## 📡 Endpoints API REST

### Conductores

- `POST /api/v1/conductores/` - Crear conductor
- `GET /api/v1/conductores/` - Listar conductores
- `GET /api/v1/conductores/disponibles` - Conductores disponibles
- `GET /api/v1/conductores/{id}` - Obtener conductor
- `PUT /api/v1/conductores/{id}` - Actualizar conductor
- `PATCH /api/v1/conductores/{id}/estado` - Cambiar estado
- `DELETE /api/v1/conductores/{id}` - Eliminar conductor

### Asignaciones

- `POST /api/v1/asignaciones/automatica` - Asignación automática
- `POST /api/v1/asignaciones/manual` - Asignación manual
- `GET /api/v1/asignaciones/` - Listar asignaciones
- `GET /api/v1/asignaciones/stats` - Estadísticas

## 🧪 Pruebas Rápidas

```bash
# Listar conductores de prueba
curl http://localhost:8003/api/v1/conductores/

# Conductores disponibles
curl http://localhost:8003/api/v1/conductores/disponibles

# Crear asignación automática
curl -X POST "http://localhost:8003/api/v1/asignaciones/automatica?algoritmo=round_robin" \
  -H "Content-Type: application/json" \
  -d '{
    "id_viaje": 1001,
    "id_pasajero": 500,
    "origen": "Plaza 25 de Mayo",
    "destino": "Terminal de Buses",
    "prioridad": 1
  }'

# Ver estadísticas
curl http://localhost:8003/api/v1/asignaciones/stats
```

## 🔄 Gestión de Contenedores

```bash
# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f despacho-api

# Detener servicios
docker-compose down

# Detener y limpiar todo (incluye volúmenes)
docker-compose down -v

# Reconstruir imagen
docker-compose build --no-cache

# Reiniciar un servicio específico
docker-compose restart despacho-api
```

## 📊 Arquitectura Docker

```
┌─────────────────────────────────┐
│  Docker Compose Network         │
│  (smart-ride-network)           │
│                                 │
│  ┌──────────────────────────┐  │
│  │  despacho-postgres       │  │
│  │  Port: 5432              │  │
│  └──────────────────────────┘  │
│                                 │
│  ┌──────────────────────────┐  │
│  │  despacho-rabbitmq       │  │
│  │  Ports: 5672, 15672      │  │
│  └──────────────────────────┘  │
│                                 │
│  ┌──────────────────────────┐  │
│  │  despacho-redis          │  │
│  │  Port: 6379              │  │
│  └──────────────────────────┘  │
│                                 │
│  ┌──────────────────────────┐  │
│  │  despacho-api            │  │
│  │  Port: 8003              │  │
│  │  (FastAPI + RabbitMQ)    │  │
│  └──────────────────────────┘  │
│                                 │
│  ┌──────────────────────────┐  │
│  │  despacho-grpc           │  │
│  │  Port: 50051             │  │
│  └──────────────────────────┘  │
└─────────────────────────────────┘
```

## 🧠 Algoritmos de Asignación

1. **Round Robin** - Distribuye equitativamente
2. **Por Calificación** - Mejor calificado primero
3. **Menor Carga** - Menos viajes completados
4. **Cercanía** - Más cercano (simulado)

## 🔌 Servicios gRPC

- **ConfirmarAsignacion** - Asignar conductor
- **ObtenerConductorAsignado** - Info del conductor
- **CancelarAsignacion** - Cancelar
- **VerificarDisponibilidad** - Check disponibilidad

## 🐛 Troubleshooting

### Error: puerto ya en uso
```bash
docker-compose down
lsof -ti:8003 | xargs kill -9
docker-compose up
```

### Ver logs de un servicio específico
```bash
docker-compose logs -f despacho-api
docker-compose logs -f postgres
docker-compose logs -f rabbitmq
```

### Reiniciar base de datos
```bash
docker-compose down -v
docker-compose up postgres
```

### Acceder a contenedor
```bash
docker exec -it despacho-api bash
docker exec -it despacho-postgres psql -U despacho_user -d despacho_db
```

## 👥 Autor

- Christian Paul Vidaurre Mejia

Universidad San Francisco Xavier de Chuquisaca

## 📝 Licencia

Proyecto académico - USFX 2024