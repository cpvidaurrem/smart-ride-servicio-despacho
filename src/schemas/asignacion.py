from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from src.models.asignacion import EstadoAsignacion, TipoAlgoritmo


class AsignacionBase(BaseModel):
    """Schema base para asignación"""
    id_viaje: int
    origen: str = Field(..., min_length=3, max_length=200)
    destino: str = Field(..., min_length=3, max_length=200)


class AsignacionCreate(AsignacionBase):
    """Schema para crear una asignación"""
    id_pasajero: int
    prioridad: Optional[int] = 1


class AsignacionUpdate(BaseModel):
    """Schema para actualizar una asignación"""
    estado: Optional[EstadoAsignacion] = None
    motivo_rechazo: Optional[str] = None


class AsignacionResponse(AsignacionBase):
    """Schema de respuesta"""
    id_asignacion: int
    id_conductor: int
    id_pasajero: int
    estado: EstadoAsignacion
    algoritmo_usado: TipoAlgoritmo
    prioridad: int
    tiempo_asignacion_ms: Optional[int] = None
    distancia_estimada_km: Optional[float] = None
    motivo_rechazo: Optional[str] = None
    fecha_asignacion: datetime
    fecha_actualizacion: datetime
    
    model_config = ConfigDict(from_attributes=True)