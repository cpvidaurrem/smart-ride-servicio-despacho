from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.config import settings
from src.database import init_db
from src.api import conductores, asignaciones


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionar ciclo de vida de la aplicación"""
    # Startup
    print("🚀 Iniciando Servicio de Despacho...")
    try:
        init_db()
        print("✅ Base de datos inicializada")
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
    
    yield
    
    # Shutdown
    print("👋 Deteniendo Servicio de Despacho...")


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    # Servicio de Despacho - Smart Ride
    
    Microservicio para asignación de conductores a viajes.
    
    ## Funcionalidades:
    - **Gestión de Conductores**: CRUD completo
    - **Asignación Automática**: Algoritmos inteligentes
    - **Swagger**: Documentación automática
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
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
    """Health check"""
    return {
        "status": "healthy",
        "servicio": settings.app_name,
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)