from sqlalchemy.orm import Session
from typing import List, Optional
import time
import random
from fastapi import HTTPException, status
from src.models.asignacion import Asignacion, EstadoAsignacion, TipoAlgoritmo
from src.schemas.asignacion import AsignacionCreate, AsignacionUpdate
from src.clients.users_client import users_client


class AsignacionService:
    """Servicio para gestionar asignaciones"""
    
    @staticmethod
    async def crear_asignacion_automatica_async(
        db: Session,
        asignacion_data: AsignacionCreate,
        algoritmo: TipoAlgoritmo = TipoAlgoritmo.CALIFICACION
    ) -> Optional[Asignacion]:
        """Crear asignación automática"""
        start_time = time.time()
        
        print(f"🔍 [ASIGNACION_SERVICE] Buscando conductores disponibles...")
        
        # 1. Buscar conductores disponibles
        conductores = await users_client.get_conductores_disponibles()
        
        if not conductores:
            print(f"⚠️ [ASIGNACION_SERVICE] No hay conductores disponibles")
            return None
        
        print(f"✅ [ASIGNACION_SERVICE] Encontrados {len(conductores)} conductores disponibles")
        
        # 2. Seleccionar conductor según algoritmo
        conductor_seleccionado = AsignacionService._seleccionar_conductor_local(
            conductores,
            algoritmo
        )
        
        if not conductor_seleccionado:
            print(f"⚠️ [ASIGNACION_SERVICE] No se pudo seleccionar conductor")
            return None
        
        print(f"✅ [ASIGNACION_SERVICE] Conductor seleccionado: {conductor_seleccionado['id_conductor']} (algoritmo: {algoritmo.value})")
        
        # 3. Calcular tiempo de asignación
        tiempo_ms = int((time.time() - start_time) * 1000)
        
        # 4. Crear asignación en BD
        db_asignacion = Asignacion(
            id_viaje=asignacion_data.id_viaje,
            id_conductor=conductor_seleccionado["id_conductor"],
            id_pasajero=asignacion_data.id_pasajero,
            origen=asignacion_data.origen,
            destino=asignacion_data.destino,
            estado=EstadoAsignacion.ASIGNADO,
            algoritmo_usado=algoritmo,
            prioridad=asignacion_data.prioridad or 1,
            tiempo_asignacion_ms=tiempo_ms,
            distancia_estimada_km=round(random.uniform(2.0, 15.0), 2)
        )
        
        # 5. Actualizar estado del conductor a OCUPADO
        print(f"🔄 [ASIGNACION_SERVICE] Actualizando conductor {conductor_seleccionado['id_conductor']} a ocupado")
        
        actualizado = await users_client.actualizar_estado_conductor(
            id_conductor=conductor_seleccionado["id_conductor"],
            estado="ocupado"
        )
        
        if not actualizado:
            print(f"⚠️ [ASIGNACION_SERVICE] No se pudo actualizar estado del conductor {conductor_seleccionado['id_conductor']}")
        
        # 6. Guardar en BD
        db.add(db_asignacion)
        db.commit()
        db.refresh(db_asignacion)
        
        print(f"✅ [ASIGNACION_SERVICE] Asignación creada: ID {db_asignacion.id_asignacion}")
        
        return db_asignacion
    
    @staticmethod
    def _seleccionar_conductor_local(conductores: List[dict], algoritmo: TipoAlgoritmo) -> Optional[dict]:
        """Seleccionar conductor según algoritmo"""
        if not conductores:
            return None
        
        if algoritmo == TipoAlgoritmo.CALIFICACION:
            # Ordenar por calificación descendente
            conductores_ordenados = sorted(
                conductores,
                key=lambda c: float(c.get('calificacion_promedio', 0)),
                reverse=True
            )
            return conductores_ordenados[0]
        
        elif algoritmo == TipoAlgoritmo.ROUND_ROBIN:
            # Ordenar por total de viajes ascendente
            conductores_ordenados = sorted(
                conductores,
                key=lambda c: int(c.get('total_viajes', 0))
            )
            return conductores_ordenados[0]
        
        else:
            # Por defecto, retornar el primero
            return conductores[0]
    
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
    async def actualizar_asignacion_async(
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
            await users_client.actualizar_estado_conductor(
                id_conductor=db_asignacion.id_conductor,
                estado="disponible"
            )
        
        db.commit()
        db.refresh(db_asignacion)
        return db_asignacion
    
    @staticmethod
    async def completar_asignacion_async(db: Session, asignacion_id: int) -> Asignacion:
        """Completar asignación y liberar conductor"""
        db_asignacion = AsignacionService.obtener_asignacion(db, asignacion_id)
        db_asignacion.estado = EstadoAsignacion.COMPLETADO
        
        # Liberar conductor
        await users_client.actualizar_estado_conductor(
            id_conductor=db_asignacion.id_conductor,
            estado="disponible"
        )
        
        db.commit()
        db.refresh(db_asignacion)
        return db_asignacion