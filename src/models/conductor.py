from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Float
from sqlalchemy.sql import func
from src.database import Base
import enum


class EstadoConductor(str, enum.Enum):
    """Estados posibles de un conductor"""
    DISPONIBLE = "disponible"
    OCUPADO = "ocupado"
    INACTIVO = "inactivo"
    DESCONECTADO = "desconectado"


class Conductor(Base):
    """Modelo de conductor para asignación de viajes"""
    
    __tablename__ = "conductores"
    
    id_conductor = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, nullable=False, unique=True, index=True)
    nombre_completo = Column(String(200), nullable=False)
    licencia = Column(String(50), nullable=False, unique=True)
    modelo_auto = Column(String(100), nullable=False)
    placa_auto = Column(String(20), nullable=False, unique=True)
    estado = Column(
        SQLEnum(EstadoConductor),
        default=EstadoConductor.DESCONECTADO,
        nullable=False,
        index=True
    )
    ubicacion_lat = Column(Float, nullable=True)
    ubicacion_lng = Column(Float, nullable=True)
    calificacion_promedio = Column(Float, default=5.0)
    viajes_completados = Column(Integer, default=0)
    ultima_actualizacion = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    fecha_registro = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    def __repr__(self):
        return f"<Conductor(id={self.id_conductor}, nombre={self.nombre_completo}, estado={self.estado})>"