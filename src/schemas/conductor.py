from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from src.models.conductor import EstadoConductor


class ConductorBase(BaseModel):
    """Schema base para conductor"""
    id_usuario: int = Field(..., description="ID del usuario asociado")
    nombre_completo: str = Field(..., min_length=3, max_length=200)
    licencia: str = Field(..., min_length=5, max_length=50)
    modelo_auto: str = Field(..., min_length=3, max_length=100)
    placa_auto: str = Field(..., min_length=4, max_length=20)


class ConductorCreate(ConductorBase):
    """Schema para crear un conductor"""
    pass


class ConductorUpdate(BaseModel):
    """Schema para actualizar un conductor"""
    nombre_completo: Optional[str] = Field(None, min_length=3, max_length=200)
    modelo_auto: Optional[str] = Field(None, min_length=3, max_length=100)
    placa_auto: Optional[str] = Field(None, min_length=4, max_length=20)
    estado: Optional[EstadoConductor] = None
    ubicacion_lat: Optional[float] = None
    ubicacion_lng: Optional[float] = None


class ConductorEstadoUpdate(BaseModel):
    """Schema para actualizar solo el estado del conductor"""
    estado: EstadoConductor = Field(..., description="Nuevo estado del conductor")


class ConductorUbicacionUpdate(BaseModel):
    """Schema para actualizar la ubicación del conductor"""
    ubicacion_lat: float = Field(..., ge=-90, le=90)
    ubicacion_lng: float = Field(..., ge=-180, le=180)


class ConductorResponse(ConductorBase):
    """Schema de respuesta para conductor"""
    id_conductor: int
    estado: EstadoConductor
    ubicacion_lat: Optional[float] = None
    ubicacion_lng: Optional[float] = None
    calificacion_promedio: float
    viajes_completados: int
    ultima_actualizacion: datetime
    fecha_registro: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ConductorDisponible(BaseModel):
    """Schema simplificado de conductor disponible"""
    id_conductor: int
    nombre_completo: str
    modelo_auto: str
    placa_auto: str
    calificacion_promedio: float
    viajes_completados: int
    ubicacion_lat: Optional[float] = None
    ubicacion_lng: Optional[float] = None