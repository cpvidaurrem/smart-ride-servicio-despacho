from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from src.models.asignacion import EstadoAsignacion, TipoAlgoritmo


class AsignacionBase(BaseModel):
    """Schema base para asignación"""
    id_viaje: int = Field(..., description="ID del viaje a asignar")
    origen: str = Field(..., min_length=3, max_length=200)
    destino: str = Field(..., min_length=3, max_length=200)


class AsignacionCreate(AsignacionBase):
    """Schema para crear una asignación"""
    id_pasajero: int = Field(..., description="ID del pasajero")
    prioridad: Optional[int] = Field(1, ge=1, le=5)


class AsignacionManual(BaseModel):
    """Schema para asignación manual de conductor"""
    id_viaje: int = Field(..., description="ID del viaje")
    id_conductor: int = Field(..., description="ID del conductor")
    id_pasajero: int = Field(..., description="ID del pasajero")
    origen: str = Field(..., min_length=3, max_length=200)
    destino: str = Field(..., min_length=3, max_length=200)


class AsignacionUpdate(BaseModel):
    """Schema para actualizar una asignación"""
    estado: Optional[EstadoAsignacion] = None
    motivo_rechazo: Optional[str] = None


class AsignacionResponse(AsignacionBase):
    """Schema de respuesta para asignación"""
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


class AsignacionStats(BaseModel):
    """Estadísticas de asignaciones"""
    total_asignaciones: int
    asignaciones_exitosas: int
    asignaciones_rechazadas: int
    asignaciones_canceladas: int
    tiempo_promedio_ms: Optional[float] = None
    algoritmo_mas_usado: Optional[str] = None


class SolicitudAsignacionRabbitMQ(BaseModel):
    """Schema para mensajes de RabbitMQ de nuevas reservas"""
    id_viaje: int
    id_pasajero: int
    origen: str
    destino: str
    prioridad: Optional[int] = 1
    timestamp: str