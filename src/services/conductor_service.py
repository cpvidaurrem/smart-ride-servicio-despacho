from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from fastapi import HTTPException, status
from src.models.conductor import Conductor, EstadoConductor
from src.schemas.conductor import ConductorCreate, ConductorUpdate


class ConductorService:
    """Servicio para gestionar conductores"""
    
    @staticmethod
    def crear_conductor(db: Session, conductor: ConductorCreate) -> Conductor:
        """Crear un nuevo conductor"""
        try:
            db_conductor = Conductor(
                id_usuario=conductor.id_usuario,
                nombre_completo=conductor.nombre_completo,
                licencia=conductor.licencia,
                modelo_auto=conductor.modelo_auto,
                placa_auto=conductor.placa_auto,
                estado=EstadoConductor.DESCONECTADO
            )
            db.add(db_conductor)
            db.commit()
            db.refresh(db_conductor)
            return db_conductor
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El conductor ya existe o hay datos duplicados"
            )
    
    @staticmethod
    def obtener_conductor(db: Session, conductor_id: int) -> Conductor:
        """Obtener un conductor por ID"""
        conductor = db.query(Conductor).filter(
            Conductor.id_conductor == conductor_id
        ).first()
        
        if not conductor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conductor {conductor_id} no encontrado"
            )
        return conductor
    
    @staticmethod
    def listar_conductores(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        estado: Optional[EstadoConductor] = None
    ) -> List[Conductor]:
        """Listar conductores"""
        query = db.query(Conductor)
        
        if estado:
            query = query.filter(Conductor.estado == estado)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def actualizar_conductor(
        db: Session,
        conductor_id: int,
        conductor_update: ConductorUpdate
    ) -> Conductor:
        """Actualizar conductor"""
        db_conductor = ConductorService.obtener_conductor(db, conductor_id)
        
        update_data = conductor_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_conductor, field, value)
        
        try:
            db.commit()
            db.refresh(db_conductor)
            return db_conductor
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error al actualizar: datos duplicados"
            )
    
    @staticmethod
    def eliminar_conductor(db: Session, conductor_id: int) -> bool:
        """Eliminar conductor (soft delete)"""
        db_conductor = ConductorService.obtener_conductor(db, conductor_id)
        db_conductor.estado = EstadoConductor.INACTIVO
        db.commit()
        return True
    
    @staticmethod
    def obtener_conductores_disponibles(db: Session) -> List[Conductor]:
        """Obtener conductores disponibles"""
        return db.query(Conductor).filter(
            Conductor.estado == EstadoConductor.DISPONIBLE
        ).all()