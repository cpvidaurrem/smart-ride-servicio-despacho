from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from src.database import Base
import enum


class EstadoAsignacion(str, enum.Enum):
    """Estados posibles de una asignación"""
    ASIGNADO = "asignado"
    ACEPTADO = "aceptado"
    RECHAZADO = "rechazado"
    CANCELADO = "cancelado"
    COMPLETADO = "completado"


class TipoAlgoritmo(str, enum.Enum):
    """Tipos de algoritmo de asignación"""
    ROUND_ROBIN = "round_robin"
    CERCANIA = "cercania"
    CALIFICACION = "calificacion"
    MENOR_CARGA = "menor_carga"


class Asignacion(Base):
    """Modelo de asignación"""
    
    __tablename__ = "asignaciones"
    
    id_asignacion = Column(Integer, primary_key=True, index=True)
    id_viaje = Column(Integer, nullable=False, index=True)
    id_conductor = Column(Integer, nullable=False, index=True)
    id_pasajero = Column(Integer, nullable=False)
    origen = Column(String(200), nullable=False)
    destino = Column(String(200), nullable=False)
    estado = Column(
        SQLEnum(EstadoAsignacion),
        default=EstadoAsignacion.ASIGNADO,
        nullable=False,
        index=True
    )
    algoritmo_usado = Column(
        SQLEnum(TipoAlgoritmo),
        default=TipoAlgoritmo.ROUND_ROBIN,
        nullable=False
    )
    prioridad = Column(Integer, default=1)
    tiempo_asignacion_ms = Column(Integer, nullable=True)
    distancia_estimada_km = Column(Float, nullable=True)
    motivo_rechazo = Column(Text, nullable=True)
    fecha_asignacion = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    fecha_actualizacion = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )