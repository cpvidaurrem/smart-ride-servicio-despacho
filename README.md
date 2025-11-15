# 🚕 Servicio de Despacho - Smart Ride

Microservicio de asignación de conductores desarrollado con **Python + FastAPI + PostgreSQL**.

## 🚀 Inicio Rápido

### 1. Clonar el repositorio
```bash
git clone <tu-repo>
cd smart-ride-servicio-despacho
```
🚀 PASO A PASO - Ejecutar el Proyecto
Perfecto! Ahora vamos a ejecutar el proyecto.
PASO 1: Verificar que todos los archivos estén en su lugar
Ejecuta este comando en la raíz del proyecto:

ls -R
```

Deberías ver algo así:
```
.:
docker-compose.yml  Dockerfile  migrations  README.md  requirements.txt  src  docker-entrypoint.sh

./migrations:
init.sql

./src:
api  config.py  database.py  main.py  models  schemas  services

./src/api:
asignaciones.py  conductores.py  __init__.py

./src/models:
asignacion.py  conductor.py  __init__.py

./src/schemas:
asignacion.py  conductor.py  __init__.py

./src/services:
asignacion_service.py  conductor_service.py  __init__.py

PASO 2: Dar permisos de ejecución al script

chmod +x docker-entrypoint.sh



PASO 3: Construir e iniciar los contenedores

### 2. Iniciar con Docker
```bash
docker-compose up --build
```

### 3. Verificar
```bash
curl http://localhost:8003/health
```

### 4. Acceder a Swagger
```
http://localhost:8003/docs
```

## 📋 Endpoints Disponibles

### Conductores
- `POST /api/v1/conductores/` - Crear conductor
- `GET /api/v1/conductores/` - Listar conductores
- `GET /api/v1/conductores/disponibles` - Conductores disponibles
- `GET /api/v1/conductores/{id}` - Obtener conductor
- `PUT /api/v1/conductores/{id}` - Actualizar conductor
- `PATCH /api/v1/conductores/{id}/estado` - Cambiar estado
- `DELETE /api/v1/conductores/{id}` - Eliminar conductor

### Asignaciones
- `POST /api/v1/asignaciones/automatica` - Crear asignación
- `GET /api/v1/asignaciones/` - Listar asignaciones
- `GET /api/v1/asignaciones/{id}` - Obtener asignación
- `PATCH /api/v1/asignaciones/{id}` - Actualizar asignación
- `POST /api/v1/asignaciones/{id}/completar` - Completar asignación

### Acceder a BD por bash
# Conectarse a PostgreSQL
docker exec -it despacho-postgres psql -U despacho_user -d despacho_db

# Ver las tablas
\dt

# Ver conductores
SELECT * FROM conductores;

# Salir
\q

## 🛠️ Tecnologías

- Python 3.11
- FastAPI
- PostgreSQL (latest)
- SQLAlchemy
- Pydantic
- Docker

## 👥 Autor

- Vidaurre Mejia Christian Paul
- kristian2vidaurre@gmail.com