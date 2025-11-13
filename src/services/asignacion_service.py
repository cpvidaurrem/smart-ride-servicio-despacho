from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import time
import random
from src.models.asignacion import Asignacion, EstadoAsignacion, TipoAlgoritmo
from src.models.conductor import Conductor, EstadoConductor
from src.schemas.asignacion import AsignacionCreate, AsignacionManual, AsignacionUpdate
from src.utils.logger import logger
from fastapi import HTTPException, status


class AsignacionService:
    """Servicio para gestionar asignaciones de viajes a conductores"""
    
    @staticmethod
    def crear_asignacion_automatica(
        db: Session,
        asignacion_data: AsignacionCreate,
        algoritmo: TipoAlgoritmo = TipoAlgoritmo.ROUND_ROBIN
    ) -> Optional[Asignacion]:
        """Crear asignación automática usando un algoritmo"""
        start_time = time.time()
        
        # Buscar conductor disponible según algoritmo
        conductor = AsignacionService._seleccionar_conductor(db, algoritmo)
        
        if not conductor:
            logger.warning(
                f"No hay conductores disponibles para viaje {asignacion_data.id_viaje}"
            )
            return None
        
        # Crear la asignación
        tiempo_ms = int((time.time() - start_time) * 1000)
        
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
            distancia_estimada_km=random.uniform(2.0, 15.0)  # Simulado
        )
        
        # Cambiar estado del conductor a ocupado
        conductor.estado = EstadoConductor.OCUPADO
        
        db.add(db_asignacion)
        db.commit()
        db.refresh(db_asignacion)
        
        logger.info(
            f"Asignación creada: viaje={asignacion_data.id_viaje}, "
            f"conductor={conductor.id_conductor}, tiempo={tiempo_ms}ms"
        )
        
        return db_asignacion
    
    @staticmethod
    def crear_asignacion_manual(
        db: Session,
        asignacion_data: AsignacionManual
    ) -> Asignacion:
        """Crear asignación manual especificando el conductor"""
        
        # Verificar que el conductor existe y está disponible
        conductor = db.query(Conductor).filter(
            Conductor.id_conductor == asignacion_data.id_conductor
        ).first()
        
        if not conductor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conductor {asignacion_data.id_conductor} no encontrado"
            )
        
        if conductor.estado != EstadoConductor.DISPONIBLE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Conductor no disponible (estado: {conductor.estado})"
            )
        
        # Crear asignación
        db_asignacion = Asignacion(
            id_viaje=asignacion_data.id_viaje,
            id_conductor=asignacion_data.id_conductor,
            id_pasajero=asignacion_data.id_pasajero,
            origen=asignacion_data.origen,
            destino=asignacion_data.destino,
            estado=EstadoAsignacion.ASIGNADO,
            algoritmo_usado=TipoAlgoritmo.ROUND_ROBIN,  # Manual
            prioridad=1
        )
        
        conductor.estado = EstadoConductor.OCUPADO
        
        db.add(db_asignacion)
        db.commit()
        db.refresh(db_asignacion)
        
        logger.info(f"Asignación manual creada: {db_asignacion.id_asignacion}")
        return db_asignacion
    
    @staticmethod
    def _seleccionar_conductor(
        db: Session,
        algoritmo: TipoAlgoritmo
    ) -> Optional[Conductor]:
        """Seleccionar un conductor según el algoritmo especificado"""
        
        conductores_disponibles = db.query(Conductor).filter(
            Conductor.estado == EstadoConductor.DISPONIBLE
        )
        
        if algoritmo == TipoAlgoritmo.ROUND_ROBIN:
            # Seleccionar el que tiene menos viajes completados
            return conductores_disponibles.order_by(
                Conductor.viajes_completados
            ).first()
        
        elif algoritmo == TipoAlgoritmo.CALIFICACION:
            # Seleccionar el mejor calificado
            return conductores_disponibles.order_by(
                Conductor.calificacion_promedio.desc()
            ).first()
        
        elif algoritmo == TipoAlgoritmo.MENOR_CARGA:
            # Seleccionar el con menos viajes completados hoy (simulado)
            return conductores_disponibles.order_by(
                Conductor.viajes_completados
            ).first()
        
        else:
            # Por defecto: aleatorio
            conductores = conductores_disponibles.all()
            return random.choice(conductores) if conductores else None
    
    @staticmethod
    def obtener_asignacion(db: Session, asignacion_id: int) -> Asignacion:
        """Obtener una asignación por ID"""
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
    def obtener_asignacion_por_viaje(db: Session, viaje_id: int) -> Optional[Asignacion]:
        """Obtener la asignación de un viaje específico"""
        return db.query(Asignacion).filter(
            Asignacion.id_viaje == viaje_id
        ).first()
    
    @staticmethod
    def listar_asignaciones(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        estado: Optional[EstadoAsignacion] = None,
        conductor_id: Optional[int] = None
    ) -> List[Asignacion]:
        """Listar asignaciones con filtros"""
        query = db.query(Asignacion)
        
        if estado:
            query = query.filter(Asignacion.estado == estado)
        
        if conductor_id:
            query = query.filter(Asignacion.id_conductor == conductor_id)
        
        return query.order_by(
            Asignacion.fecha_asignacion.desc()
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def actualizar_asignacion(
        db: Session,
        asignacion_id: int,
        asignacion_update: AsignacionUpdate
    ) -> Asignacion:
        """Actualizar el estado de una asignación"""
        db_asignacion = AsignacionService.obtener_asignacion(db, asignacion_id)
        
        estado_anterior = db_asignacion.estado
        update_data = asignacion_update.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_asignacion, field, value)
        
        # Si se rechaza o cancela, liberar al conductor
        if update_data.get("estado") in [
            EstadoAsignacion.RECHAZADO,
            EstadoAsignacion.CANCELADO
        ]:
            conductor = db.query(Conductor).filter(
                Conductor.id_conductor == db_asignacion.id_conductor
            ).first()
            if conductor:
                conductor.estado = EstadoConductor.DISPONIBLE
        
        db.commit()
        db.refresh(db_asignacion)
        
        logger.info(
            f"Asignación {asignacion_id} actualizada: "
            f"{estado_anterior} -> {db_asignacion.estado}"
        )
        
        return db_asignacion
    
    @staticmethod
    def completar_asignacion(db: Session, asignacion_id: int) -> Asignacion:
        """Marcar una asignación como completada"""
        db_asignacion = AsignacionService.obtener_asignacion(db, asignacion_id)
        
        db_asignacion.estado = EstadoAsignacion.COMPLETADO
        
        # Liberar conductor y actualizar estadísticas
        conductor = db.query(Conductor).filter(
            Conductor.id_conductor == db_asignacion.id_conductor
        ).first()
        
        if conductor:
            conductor.estado = EstadoConductor.DISPONIBLE
            conductor.viajes_completados += 1
        
        db.commit()
        db.refresh(db_asignacion)
        
        logger.info(f"Asignación {asignacion_id} completada")
        return db_asignacion
    
    @staticmethod
    def obtener_estadisticas(db: Session) -> dict:
        """Obtener estadísticas de asignaciones"""
        total = db.query(func.count(Asignacion.id_asignacion)).scalar()
        
        exitosas = db.query(func.count(Asignacion.id_asignacion)).filter(
            Asignacion.estado == EstadoAsignacion.COMPLETADO
        ).scalar()
        
        rechazadas = db.query(func.count(Asignacion.id_asignacion)).filter(
            Asignacion.estado == EstadoAsignacion.RECHAZADO
        ).scalar()
        
        canceladas = db.query(func.count(Asignacion.id_asignacion)).filter(
            Asignacion.estado == EstadoAsignacion.CANCELADO
        ).scalar()
        
        tiempo_promedio = db.query(
            func.avg(Asignacion.tiempo_asignacion_ms)
        ).scalar()
        
        return {
            "total_asignaciones": total or 0,
            "asignaciones_exitosas": exitosas or 0,
            "asignaciones_rechazadas": rechazadas or 0,
            "asignaciones_canceladas": canceladas or 0,
            "tiempo_promedio_ms": float(tiempo_promedio) if tiempo_promedio else None
        }