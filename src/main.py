from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from src.config import settings
from src.database import init_db
from src.api import asignaciones
from src.events import init_rabbitmq, close_rabbitmq, start_consumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionar ciclo de vida de la aplicación"""
    # Startup
    print("🚀 Iniciando Servicio de Despacho...")
    
    try:
        # Inicializar base de datos
        init_db()
        print("✅ Base de datos inicializada")
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
    
    try:
        # Inicializar RabbitMQ
        await init_rabbitmq()
        print("✅ RabbitMQ inicializado")
        
        # Iniciar consumer en background
        asyncio.create_task(start_consumer())
        print("✅ Consumer de eventos iniciado")
    except Exception as e:
        print(f"❌ Error inicializando RabbitMQ: {e}")
    
    yield
    
    # Shutdown
    print("👋 Deteniendo Servicio de Despacho...")
    await close_rabbitmq()


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    # 🚕 Servicio de Despacho - Smart Ride
    
    Microservicio para **asignación automática** de conductores a viajes.
    
    ## 🎯 Funcionalidades:
    
    ### 📡 Event-Driven Architecture
    - Escucha eventos de **nueva reserva** desde RabbitMQ
    - Asigna conductor automáticamente
    - Publica eventos de confirmación/fallo
    
    ### 🤖 Algoritmos de Asignación
    - **Round Robin**: Distribuye equitativamente los viajes
    - **Calificación**: Prioriza conductores mejor valorados
    - **Cercanía**: Basado en ubicación (próximamente)
    
    ### 🔗 Integración con Servicios
    - **Users Service**: Obtiene conductores disponibles
    - **Reservas Service**: Confirma asignaciones
    
    ## 📊 Endpoints Disponibles:
    - `POST /api/v1/asignaciones/automatica` - Asignación manual
    - `GET /api/v1/asignaciones` - Listar asignaciones
    - `PATCH /api/v1/asignaciones/{id}` - Actualizar asignación
    
    ## 🐰 Eventos RabbitMQ:
    
    ### Consume:
    - `ride.nueva_reserva` → Asigna conductor automáticamente
    
    ### Publica:
    - `dispatch.asignacion_confirmada` → Conductor asignado exitosamente
    - `dispatch.asignacion_fallida` → No hay conductores disponibles
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    swagger_ui_parameters={
        "syntaxHighlight.theme": "monokai",
        "defaultModelsExpandDepth": -1
    }
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(asignaciones.router, prefix="/api/v1")


@app.get("/", tags=["Health"])
def root():
    """Endpoint raíz"""
    return {
        "servicio": settings.app_name,
        "version": settings.app_version,
        "estado": "activo",
        "documentacion": "/docs",
        "endpoints": {
            "asignaciones": "/api/v1/asignaciones",
            "health": "/health"
        }
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "servicio": settings.app_name,
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)