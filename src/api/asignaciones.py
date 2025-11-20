from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from src.database import get_db
from src.models.asignacion import EstadoAsignacion, TipoAlgoritmo
from src.schemas.asignacion import (
    AsignacionCreate,
    AsignacionUpdate,
    AsignacionResponse
)
from src.services.asignacion_service import AsignacionService

router = APIRouter(prefix="/asignaciones", tags=["Asignaciones"])


@router.post(
    "/automatica",
    response_model=AsignacionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear asignación automática",
    description="""
    Crea una asignación automática de conductor a un viaje.
    
    **Algoritmos disponibles:**
    - `round_robin`: Asigna al conductor con menos viajes
    - `calificacion`: Asigna al conductor mejor calificado
    - `cercania`: Asigna al conductor más cercano (futuro)
    """
)
async def crear_asignacion_automatica(
    asignacion: AsignacionCreate,
    algoritmo: TipoAlgoritmo = Query(TipoAlgoritmo.CALIFICACION, description="Algoritmo de asignación"),
    db: Session = Depends(get_db)
):
    """Crear asignación automática"""
    result = await AsignacionService.crear_asignacion_automatica_async(db, asignacion, algoritmo)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No hay conductores disponibles en este momento"
        )
    
    return result


@router.get(
    "/",
    response_model=List[AsignacionResponse],
    summary="Listar asignaciones",
    description="Obtiene la lista de todas las asignaciones con filtros opcionales"
)
def listar_asignaciones(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=500, description="Máximo de registros"),
    estado: Optional[EstadoAsignacion] = Query(None, description="Filtrar por estado"),
    db: Session = Depends(get_db)
):
    """Listar asignaciones"""
    return AsignacionService.listar_asignaciones(db, skip, limit, estado)


@router.get(
    "/{asignacion_id}",
    response_model=AsignacionResponse,
    summary="Obtener asignación",
    description="Obtiene los detalles de una asignación específica"
)
def obtener_asignacion(
    asignacion_id: int,
    db: Session = Depends(get_db)
):
    """Obtener asignación por ID"""
    return AsignacionService.obtener_asignacion(db, asignacion_id)


@router.patch(
    "/{asignacion_id}",
    response_model=AsignacionResponse,
    summary="Actualizar asignación",
    description="Actualiza el estado o información de una asignación"
)
async def actualizar_asignacion(
    asignacion_id: int,
    asignacion_update: AsignacionUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar asignación"""
    return await AsignacionService.actualizar_asignacion_async(db, asignacion_id, asignacion_update)


@router.post(
    "/{asignacion_id}/completar",
    response_model=AsignacionResponse,
    summary="Completar asignación",
    description="Marca una asignación como completada y libera al conductor"
)
async def completar_asignacion(
    asignacion_id: int,
    db: Session = Depends(get_db)
):
    """Completar asignación"""
    return await AsignacionService.completar_asignacion_async(db, asignacion_id)