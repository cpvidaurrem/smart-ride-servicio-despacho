from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from src.database import get_db
from src.models.asignacion import EstadoAsignacion, TipoAlgoritmo
from src.schemas.asignacion import (
    AsignacionCreate,
    AsignacionManual,
    AsignacionUpdate,
    AsignacionResponse,
    AsignacionStats
)
from src.services.asignacion_service import AsignacionService

router = APIRouter(prefix="/asignaciones", tags=["Asignaciones"])


@router.post(
    "/automatica",
    response_model=AsignacionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear asignación automática"
)
def crear_asignacion_automatica(
    asignacion: AsignacionCreate,
    algoritmo: TipoAlgoritmo = Query(
        TipoAlgoritmo.ROUND_ROBIN,
        description="Algoritmo de asignación a usar"
    ),
    db: Session = Depends(get_db)
):
    """
    Crear una asignación automática de conductor usando un algoritmo.
    
    Algoritmos disponibles:
    - **round_robin**: Distribuye equitativamente entre conductores
    - **calificacion**: Asigna al conductor mejor calificado
    - **menor_carga**: Asigna al conductor con menos viajes completados
    - **cercania**: Asigna al conductor más cercano (simulado)
    """
    result = AsignacionService.crear_asignacion_automatica(db, asignacion, algoritmo)
    
    if not result:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No hay conductores disponibles en este momento"
        )
    
    return result


@router.post(
    "/manual",
    response_model=AsignacionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear asignación manual"
)
def crear_asignacion_manual(
    asignacion: AsignacionManual,
    db: Session = Depends(get_db)
):
    """
    Crear una asignación manual especificando el conductor.
    """
    return AsignacionService.crear_asignacion_manual(db, asignacion)


@router.get(
    "/",
    response_model=List[AsignacionResponse],
    summary="Listar asignaciones"
)
def listar_asignaciones(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    estado: Optional[EstadoAsignacion] = Query(None),
    conductor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Obtener lista de asignaciones con filtros opcionales.
    """
    return AsignacionService.listar_asignaciones(
        db, skip, limit, estado, conductor_id
    )


@router.get(
    "/stats",
    response_model=AsignacionStats,
    summary="Obtener estadísticas"
)
def obtener_estadisticas(db: Session = Depends(get_db)):
    """
    Obtener estadísticas generales de asignaciones.
    """
    stats = AsignacionService.obtener_estadisticas(db)
    return AsignacionStats(**stats)


@router.get(
    "/{asignacion_id}",
    response_model=AsignacionResponse,
    summary="Obtener asignación por ID"
)
def obtener_asignacion(
    asignacion_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener información detallada de una asignación específica.
    """
    return AsignacionService.obtener_asignacion(db, asignacion_id)


@router.get(
    "/viaje/{viaje_id}",
    response_model=AsignacionResponse,
    summary="Obtener asignación por ID de viaje"
)
def obtener_asignacion_por_viaje(
    viaje_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener la asignación asociada a un viaje específico.
    """
    from fastapi import HTTPException
    asignacion = AsignacionService.obtener_asignacion_por_viaje(db, viaje_id)
    
    if not asignacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe asignación para el viaje {viaje_id}"
        )
    
    return asignacion


@router.patch(
    "/{asignacion_id}",
    response_model=AsignacionResponse,
    summary="Actualizar asignación"
)
def actualizar_asignacion(
    asignacion_id: int,
    asignacion_update: AsignacionUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualizar el estado de una asignación.
    """
    return AsignacionService.actualizar_asignacion(db, asignacion_id, asignacion_update)


@router.post(
    "/{asignacion_id}/completar",
    response_model=AsignacionResponse,
    summary="Completar asignación"
)
def completar_asignacion(
    asignacion_id: int,
    db: Session = Depends(get_db)
):
    """
    Marcar una asignación como completada.
    """
    return AsignacionService.completar_asignacion(db, asignacion_id)