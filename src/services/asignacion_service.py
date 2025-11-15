from sqlalchemy.orm import Session
from typing import List, Optional
import time
import random
from fastapi import HTTPException, status
from src.models.asignacion import Asignacion, EstadoAsignacion, TipoAlgoritmo
from src.models.conductor import Conductor, EstadoConductor
from src.schemas.asignacion import AsignacionCreate, AsignacionUpdate


class AsignacionService:
    """Servicio para gestionar asignaciones"""
    
    @staticmethod
    def crear_asignacion_automatica(
        db: Session,
        asignacion_data: AsignacionCreate,
        algoritmo: TipoAlgoritmo = TipoAlgoritmo.ROUND_ROBIN
    ) -> Optional[Asignacion]:
        """Crear asignación automática"""
        start_time = time.time()
        
        # Buscar conductor disponible
        conductor = AsignacionService._seleccionar_conductor(db, algoritmo)
        
        if not conductor:
            return None
        
        # Calcular tiempo de asignación
        tiempo_ms = int((time.time() - start_time) * 1000)
        
        # Crear asignación
        db_asignacion = Asignacion(
            id_viaje=asignacion_data.id_viaje,
            id_conductor=conductor.id_conductor,
            id_pasajero=asignacion_data.id_pasajero,
            origen=asignacion_data.origen,
            destino=asignacion_data.destino,
            estado=EstadoAsignacion.ASIGNADO,
            algoritmo_usado=algoritmo,
            prioridad=asignacion_data.prioridad or 1,
            tiempo_asignacion_ms=tiempo_ms,
            distancia_estimada_km=random.uniform(2.0, 15.0)
        )
        
        # Cambiar estado del conductor
        conductor.estado = EstadoConductor.OCUPADO
        
        db.add(db_asignacion)
        db.commit()
        db.refresh(db_asignacion)
        
        return db_asignacion
    
    @staticmethod
    def _seleccionar_conductor(
        db: Session,
        algoritmo: TipoAlgoritmo
    ) -> Optional[Conductor]:
        """Seleccionar conductor según algoritmo"""
        conductores = db.query(Conductor).filter(
            Conductor.estado == EstadoConductor.DISPONIBLE
        )
        
        if algoritmo == TipoAlgoritmo.ROUND_ROBIN:
            return conductores.order_by(Conductor.viajes_completados).first()
        elif algoritmo == TipoAlgoritmo.CALIFICACION:
            return conductores.order_by(Conductor.calificacion_promedio.desc()).first()
        else:
            conductores_list = conductores.all()
            return random.choice(conductores_list) if conductores_list else None
    
    @staticmethod
    def obtener_asignacion(db: Session, asignacion_id: int) -> Asignacion:
        """Obtener asignación por ID"""
        asignacion = db.query(Asignacion).filter(
            Asignacion.id_asignacion == asignacion_id
        ).first()
        
        if not asignacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asignación {asignacion_id} no encontrada"
            )
        return asignacion
    
    @staticmethod
    def listar_asignaciones(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        estado: Optional[EstadoAsignacion] = None
    ) -> List[Asignacion]:
        """Listar asignaciones"""
        query = db.query(Asignacion)
        
        if estado:
            query = query.filter(Asignacion.estado == estado)
        
        return query.order_by(
            Asignacion.fecha_asignacion.desc()
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def actualizar_asignacion(
        db: Session,
        asignacion_id: int,
        asignacion_update: AsignacionUpdate
    ) -> Asignacion:
        """Actualizar asignación"""
        db_asignacion = AsignacionService.obtener_asignacion(db, asignacion_id)
        
        update_data = asignacion_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_asignacion, field, value)
        
        # Si se rechaza o cancela, liberar conductor
        if update_data.get("estado") in [EstadoAsignacion.RECHAZADO, EstadoAsignacion.CANCELADO]:
            conductor = db.query(Conductor).filter(
                Conductor.id_conductor == db_asignacion.id_conductor
            ).first()
            if conductor:
                conductor.estado = EstadoConductor.DISPONIBLE
        
        db.commit()
        db.refresh(db_asignacion)
        return db_asignacion
    
    @staticmethod
    def completar_asignacion(db: Session, asignacion_id: int) -> Asignacion:
        """Completar asignación"""
        db_asignacion = AsignacionService.obtener_asignacion(db, asignacion_id)
        db_asignacion.estado = EstadoAsignacion.COMPLETADO
        
        # Liberar conductor y actualizar contador
        conductor = db.query(Conductor).filter(
            Conductor.id_conductor == db_asignacion.id_conductor
        ).first()
        
        if conductor:
            conductor.estado = EstadoConductor.DISPONIBLE
            conductor.viajes_completados += 1
        
        db.commit()
        db.refresh(db_asignacion)
        return db_asignacion