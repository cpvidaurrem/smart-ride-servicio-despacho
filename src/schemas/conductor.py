from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from src.models.conductor import EstadoConductor


class ConductorBase(BaseModel):
    """Schema base para conductor"""
    id_usuario: int
    nombre_completo: str = Field(..., min_length=3, max_length=200)
    licencia: str = Field(..., min_length=5, max_length=50)
    modelo_auto: str = Field(..., min_length=3, max_length=100)
    placa_auto: str = Field(..., min_length=4, max_length=20)


class ConductorCreate(ConductorBase):
    """Schema para crear un conductor"""
    pass


class ConductorUpdate(BaseModel):
    """Schema para actualizar un conductor"""
    nombre_completo: Optional[str] = None
    modelo_auto: Optional[str] = None
    placa_auto: Optional[str] = None
    estado: Optional[EstadoConductor] = None
    ubicacion_lat: Optional[float] = None
    ubicacion_lng: Optional[float] = None


class ConductorEstadoUpdate(BaseModel):
    """Schema para actualizar estado"""
    estado: EstadoConductor


class ConductorResponse(ConductorBase):
    """Schema de respuesta"""
    id_conductor: int
    estado: EstadoConductor
    ubicacion_lat: Optional[float] = None
    ubicacion_lng: Optional[float] = None
    calificacion_promedio: float
    viajes_completados: int
    ultima_actualizacion: datetime
    fecha_registro: datetime
    
    model_config = ConfigDict(from_attributes=True)