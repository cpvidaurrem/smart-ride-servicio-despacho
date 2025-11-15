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


@router.post("/automatica", response_model=AsignacionResponse, status_code=status.HTTP_201_CREATED)
def crear_asignacion_automatica(
    asignacion: AsignacionCreate,
    algoritmo: TipoAlgoritmo = Query(TipoAlgoritmo.ROUND_ROBIN),
    db: Session = Depends(get_db)
):
    """Crear asignación automática"""
    result = AsignacionService.crear_asignacion_automatica(db, asignacion, algoritmo)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No hay conductores disponibles"
        )
    
    return result


@router.get("/", response_model=List[AsignacionResponse])
def listar_asignaciones(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    estado: Optional[EstadoAsignacion] = Query(None),
    db: Session = Depends(get_db)
):
    """Listar asignaciones"""
    return AsignacionService.listar_asignaciones(db, skip, limit, estado)


@router.get("/{asignacion_id}", response_model=AsignacionResponse)
def obtener_asignacion(asignacion_id: int, db: Session = Depends(get_db)):
    """Obtener asignación por ID"""
    return AsignacionService.obtener_asignacion(db, asignacion_id)


@router.patch("/{asignacion_id}", response_model=AsignacionResponse)
def actualizar_asignacion(
    asignacion_id: int,
    asignacion_update: AsignacionUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar asignación"""
    return AsignacionService.actualizar_asignacion(db, asignacion_id, asignacion_update)


@router.post("/{asignacion_id}/completar", response_model=AsignacionResponse)
def completar_asignacion(asignacion_id: int, db: Session = Depends(get_db)):
    """Completar asignación"""
    return AsignacionService.completar_asignacion(db, asignacion_id)