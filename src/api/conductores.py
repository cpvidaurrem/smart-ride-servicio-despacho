from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from src.database import get_db
from src.models.conductor import EstadoConductor
from src.schemas.conductor import (
    ConductorCreate,
    ConductorUpdate,
    ConductorResponse,
    ConductorEstadoUpdate
)
from src.services.conductor_service import ConductorService

router = APIRouter(prefix="/conductores", tags=["Conductores"])


@router.post("/", response_model=ConductorResponse, status_code=status.HTTP_201_CREATED)
def crear_conductor(conductor: ConductorCreate, db: Session = Depends(get_db)):
    """Crear un nuevo conductor"""
    return ConductorService.crear_conductor(db, conductor)


@router.get("/", response_model=List[ConductorResponse])
def listar_conductores(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    estado: Optional[EstadoConductor] = Query(None),
    db: Session = Depends(get_db)
):
    """Listar conductores con filtros"""
    return ConductorService.listar_conductores(db, skip, limit, estado)


@router.get("/disponibles", response_model=List[ConductorResponse])
def obtener_conductores_disponibles(db: Session = Depends(get_db)):
    """Obtener conductores disponibles"""
    return ConductorService.obtener_conductores_disponibles(db)


@router.get("/{conductor_id}", response_model=ConductorResponse)
def obtener_conductor(conductor_id: int, db: Session = Depends(get_db)):
    """Obtener conductor por ID"""
    return ConductorService.obtener_conductor(db, conductor_id)


@router.put("/{conductor_id}", response_model=ConductorResponse)
def actualizar_conductor(
    conductor_id: int,
    conductor_update: ConductorUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar conductor"""
    return ConductorService.actualizar_conductor(db, conductor_id, conductor_update)


@router.patch("/{conductor_id}/estado", response_model=ConductorResponse)
def cambiar_estado(
    conductor_id: int,
    estado_update: ConductorEstadoUpdate,
    db: Session = Depends(get_db)
):
    """Cambiar estado del conductor"""
    db_conductor = ConductorService.obtener_conductor(db, conductor_id)
    conductor_update = ConductorUpdate(estado=estado_update.estado)
    return ConductorService.actualizar_conductor(db, conductor_id, conductor_update)


@router.delete("/{conductor_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_conductor(conductor_id: int, db: Session = Depends(get_db)):
    """Eliminar conductor"""
    ConductorService.eliminar_conductor(db, conductor_id)
    return None