from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from src.database import get_db
from src.models.conductor import EstadoConductor
from src.schemas.conductor import (
    ConductorCreate,
    ConductorUpdate,
    ConductorResponse,
    ConductorEstadoUpdate,
    ConductorUbicacionUpdate,
    ConductorDisponible
)
from src.services.conductor_service import ConductorService

router = APIRouter(prefix="/conductores", tags=["Conductores"])


@router.post(
    "/",
    response_model=ConductorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo conductor"
)
def crear_conductor(
    conductor: ConductorCreate,
    db: Session = Depends(get_db)
):
    """
    Crear un nuevo conductor en el sistema.
    
    - **id_usuario**: ID del usuario en el servicio de autenticación
    - **nombre_completo**: Nombre completo del conductor
    - **licencia**: Número de licencia de conducir
    - **modelo_auto**: Modelo del vehículo
    - **placa_auto**: Placa del vehículo
    """
    return ConductorService.crear_conductor(db, conductor)


@router.get(
    "/",
    response_model=List[ConductorResponse],
    summary="Listar conductores"
)
def listar_conductores(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=500, description="Límite de registros"),
    estado: Optional[EstadoConductor] = Query(None, description="Filtrar por estado"),
    db: Session = Depends(get_db)
):
    """
    Obtener lista de conductores con paginación y filtros opcionales.
    """
    return ConductorService.listar_conductores(db, skip, limit, estado)


@router.get(
    "/disponibles",
    response_model=List[ConductorDisponible],
    summary="Obtener conductores disponibles"
)
def obtener_conductores_disponibles(db: Session = Depends(get_db)):
    """
    Obtener todos los conductores que están actualmente disponibles
    para aceptar viajes.
    """
    conductores = ConductorService.obtener_conductores_disponibles(db)
    return [
        ConductorDisponible(
            id_conductor=c.id_conductor,
            nombre_completo=c.nombre_completo,
            modelo_auto=c.modelo_auto,
            placa_auto=c.placa_auto,
            calificacion_promedio=c.calificacion_promedio,
            viajes_completados=c.viajes_completados,
            ubicacion_lat=c.ubicacion_lat,
            ubicacion_lng=c.ubicacion_lng
        )
        for c in conductores
    ]


@router.get(
    "/{conductor_id}",
    response_model=ConductorResponse,
    summary="Obtener conductor por ID"
)
def obtener_conductor(
    conductor_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener información detallada de un conductor específico.
    """
    return ConductorService.obtener_conductor(db, conductor_id)


@router.put(
    "/{conductor_id}",
    response_model=ConductorResponse,
    summary="Actualizar conductor"
)
def actualizar_conductor(
    conductor_id: int,
    conductor_update: ConductorUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualizar información de un conductor existente.
    """
    return ConductorService.actualizar_conductor(db, conductor_id, conductor_update)


@router.patch(
    "/{conductor_id}/estado",
    response_model=ConductorResponse,
    summary="Cambiar estado del conductor"
)
def cambiar_estado_conductor(
    conductor_id: int,
    estado_update: ConductorEstadoUpdate,
    db: Session = Depends(get_db)
):
    """
    Cambiar el estado de disponibilidad de un conductor.
    
    Estados posibles:
    - **disponible**: Listo para aceptar viajes
    - **ocupado**: En un viaje actualmente
    - **inactivo**: No disponible temporalmente
    - **desconectado**: Fuera de línea
    """
    return ConductorService.cambiar_estado(db, conductor_id, estado_update.estado)


@router.patch(
    "/{conductor_id}/ubicacion",
    response_model=ConductorResponse,
    summary="Actualizar ubicación del conductor"
)
def actualizar_ubicacion_conductor(
    conductor_id: int,
    ubicacion: ConductorUbicacionUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualizar la ubicación geográfica del conductor.
    """
    return ConductorService.actualizar_ubicacion(
        db,
        conductor_id,
        ubicacion.ubicacion_lat,
        ubicacion.ubicacion_lng
    )


@router.delete(
    "/{conductor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar conductor"
)
def eliminar_conductor(
    conductor_id: int,
    db: Session = Depends(get_db)
):
    """
    Eliminar un conductor (soft delete - marca como inactivo).
    """
    ConductorService.eliminar_conductor(db, conductor_id)
    return None