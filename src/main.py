from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import threading
from src.config import settings
from src.database import init_db
from src.api import conductores, asignaciones
from src.messaging.rabbitmq_consumer import RabbitMQConsumer
from src.utils.logger import logger


# Variable global para el consumidor de RabbitMQ
rabbitmq_consumer = None
consumer_thread = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionar el ciclo de vida de la aplicación"""
    # Startup
    logger.info("Iniciando Servicio de Despacho...")
    
    # Inicializar base de datos
    try:
        init_db()
        logger.info("Base de datos inicializada")
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {str(e)}")
    
    # Iniciar consumidor de RabbitMQ en un hilo separado
    global rabbitmq_consumer, consumer_thread
    try:
        rabbitmq_consumer = RabbitMQConsumer()
        consumer_thread = threading.Thread(
            target=rabbitmq_consumer.iniciar_consumo,
            daemon=True
        )
        consumer_thread.start()
        logger.info("Consumidor RabbitMQ iniciado")
    except Exception as e:
        logger.error(f"Error iniciando consumidor RabbitMQ: {str(e)}")
    
    yield
    
    # Shutdown
    logger.info("Deteniendo Servicio de Despacho...")
    if rabbitmq_consumer:
        try:
            rabbitmq_consumer.detener()
        except Exception as e:
            logger.error(f"Error deteniendo consumidor: {str(e)}")


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    # Servicio de Despacho - Smart Ride
    
    Microservicio encargado de la asignación automática de conductores a solicitudes de viaje.
    
    ## Funcionalidades principales:
    
    - **Gestión de Conductores**: CRUD completo para conductores
    - **Asignación Automática**: Algoritmos inteligentes de asignación
    - **Comunicación gRPC**: Para integrarse con el servicio de reservas
    - **Mensajería Asíncrona**: Consumo de eventos desde RabbitMQ
    - **Alta Concurrencia**: Diseñado para manejar miles de solicitudes simultáneas
    
    ## Algoritmos de asignación disponibles:
    
    - **Round Robin**: Distribución equitativa entre conductores
    - **Por Calificación**: Asigna al conductor mejor calificado
    - **Menor Carga**: Asigna al conductor con menos viajes completados
    - **Cercanía**: Asigna al conductor más cercano (simulado)
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(conductores.router, prefix="/api/v1")
app.include_router(asignaciones.router, prefix="/api/v1")


@app.get("/", tags=["Health"])
def root():
    """Endpoint raíz"""
    return {
        "servicio": settings.app_name,
        "version": settings.app_version,
        "estado": "activo",
        "documentacion": "/docs"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check del servicio"""
    return {
        "status": "healthy",
        "servicio": settings.app_name,
        "version": settings.app_version,
        "rabbitmq": "connected" if rabbitmq_consumer else "disconnected"
    }


@app.get("/api/v1/info", tags=["Info"])
def service_info():
    """Información detallada del servicio"""
    return {
        "nombre": settings.app_name,
        "version": settings.app_version,
        "ambiente": settings.environment,
        "puerto": settings.port,
        "grpc_puerto": settings.grpc_port,
        "tecnologias": {
            "framework": "FastAPI",
            "lenguaje": "Python 3.11+",
            "base_datos": "PostgreSQL",
            "mensajeria": "RabbitMQ",
            "rpc": "gRPC"
        },
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "conductores": "/api/v1/conductores",
            "asignaciones": "/api/v1/asignaciones"
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Manejador global de excepciones"""
    logger.error(f"Error no controlado: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Error interno del servidor",
            "detalle": str(exc) if settings.debug else "Contacte al administrador"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )