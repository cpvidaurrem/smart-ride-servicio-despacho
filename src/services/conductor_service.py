from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from src.models.conductor import Conductor, EstadoConductor
from src.schemas.conductor import ConductorCreate, ConductorUpdate
from src.utils.logger import logger
from fastapi import HTTPException, status


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
            
            logger.info(f"Conductor creado: {db_conductor.id_conductor}")
            return db_conductor
            
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Error de integridad al crear conductor: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El conductor ya existe o hay datos duplicados (licencia, placa, id_usuario)"
            )
    
    @staticmethod
    def obtener_conductor(db: Session, conductor_id: int) -> Optional[Conductor]:
        """Obtener un conductor por ID"""
        conductor = db.query(Conductor).filter(
            Conductor.id_conductor == conductor_id
        ).first()
        
        if not conductor:
            logger.warning(f"Conductor {conductor_id} no encontrado")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conductor con ID {conductor_id} no encontrado"
            )
        
        return conductor
    
    @staticmethod
    def listar_conductores(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        estado: Optional[EstadoConductor] = None
    ) -> List[Conductor]:
        """Listar conductores con filtros opcionales"""
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
        """Actualizar información de un conductor"""
        db_conductor = ConductorService.obtener_conductor(db, conductor_id)
        
        update_data = conductor_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_conductor, field, value)
        
        try:
            db.commit()
            db.refresh(db_conductor)
            logger.info(f"Conductor {conductor_id} actualizado")
            return db_conductor
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error al actualizar: datos duplicados"
            )
    
    @staticmethod
    def cambiar_estado(
        db: Session,
        conductor_id: int,
        nuevo_estado: EstadoConductor
    ) -> Conductor:
        """Cambiar el estado de un conductor"""
        db_conductor = ConductorService.obtener_conductor(db, conductor_id)
        
        estado_anterior = db_conductor.estado
        db_conductor.estado = nuevo_estado
        
        db.commit()
        db.refresh(db_conductor)
        
        logger.info(
            f"Conductor {conductor_id} cambió de estado: "
            f"{estado_anterior} -> {nuevo_estado}"
        )
        return db_conductor
    
    @staticmethod
    def actualizar_ubicacion(
        db: Session,
        conductor_id: int,
        lat: float,
        lng: float
    ) -> Conductor:
        """Actualizar la ubicación de un conductor"""
        db_conductor = ConductorService.obtener_conductor(db, conductor_id)
        
        db_conductor.ubicacion_lat = lat
        db_conductor.ubicacion_lng = lng
        
        db.commit()
        db.refresh(db_conductor)
        
        logger.debug(f"Ubicación actualizada para conductor {conductor_id}")
        return db_conductor
    
    @staticmethod
    def eliminar_conductor(db: Session, conductor_id: int) -> bool:
        """Eliminar un conductor (soft delete cambiando estado)"""
        db_conductor = ConductorService.obtener_conductor(db, conductor_id)
        
        db_conductor.estado = EstadoConductor.INACTIVO
        db.commit()
        
        logger.info(f"Conductor {conductor_id} marcado como inactivo")
        return True
    
    @staticmethod
    def obtener_conductores_disponibles(db: Session) -> List[Conductor]:
        """Obtener todos los conductores disponibles"""
        return db.query(Conductor).filter(
            Conductor.estado == EstadoConductor.DISPONIBLE
        ).all()
    
    @staticmethod
    def incrementar_viajes_completados(db: Session, conductor_id: int):
        """Incrementar el contador de viajes completados"""
        db_conductor = ConductorService.obtener_conductor(db, conductor_id)
        db_conductor.viajes_completados += 1
        db.commit()
        logger.info(f"Viajes completados incrementado para conductor {conductor_id}")