from typing import Dict, Any
from sqlalchemy.orm import Session
import time
import random
import traceback
from src.database import SessionLocal
from src.services.asignacion_service import AsignacionService
from src.schemas.asignacion import AsignacionCreate
from src.models.asignacion import TipoAlgoritmo
from src.clients.grpc_client import reservas_grpc_client
from src.clients.users_client import users_client
from src.events.publisher import publish_event


async def handle_nueva_reserva(data: Dict[str, Any]):
    """
    Handler para evento: ride.nueva_reserva
    
    Flujo:
    1. Recibe evento de nueva reserva
    2. Busca conductor disponible
    3. Crea asignación en BD
    4. Confirma asignación vía gRPC a Reservas Service
    5. Publica evento de confirmación/fallo
    """
    print("=" * 60)
    print("🎯 [HANDLER] handle_nueva_reserva INICIADO")
    print("=" * 60)
    
    id_viaje = data.get('id_viaje')
    id_cliente = data.get('id_cliente')
    origen = data.get('origen')
    destino = data.get('destino')
    
    print(f"📦 Datos recibidos:")
    print(f"   - ID Viaje: {id_viaje}")
    print(f"   - ID Cliente: {id_cliente}")
    print(f"   - Origen: {origen}")
    print(f"   - Destino: {destino}")
    
    # Validar datos obligatorios
    if not all([id_viaje, id_cliente, origen, destino]):
        error_msg = f"❌ Datos incompletos - Viaje: {id_viaje}, Cliente: {id_cliente}, Origen: {origen}, Destino: {destino}"
        print(error_msg)
        
        await publish_event("dispatch.asignacion_fallida", {
            "id_viaje": id_viaje,
            "id_pasajero": id_cliente,
            "motivo": "Datos incompletos en nueva_reserva",
            "timestamp": data.get("fecha_solicitud")
        })
        return
    
    print(f"✅ Validación de datos OK")
    
    db: Session = SessionLocal()
    
    try:
        print(f"🔍 Iniciando proceso de asignación para viaje {id_viaje}")
        
        # 1. Crear asignación automática
        asignacion_data = AsignacionCreate(
            id_viaje=id_viaje,
            id_pasajero=id_cliente,
            origen=origen,
            destino=destino,
            prioridad=1
        )
        
        print(f"📝 AsignacionCreate creado")
        
        # 2. Asignar conductor (algoritmo: calificación)
        print(f"🤖 Llamando a AsignacionService.crear_asignacion_automatica_async")
        
        resultado = await AsignacionService.crear_asignacion_automatica_async(
            db=db,
            asignacion_data=asignacion_data,
            algoritmo=TipoAlgoritmo.CALIFICACION
        )
        
        if not resultado:
            print(f"⚠️ [FALLO] No hay conductores disponibles para viaje {id_viaje}")
            
            await publish_event("dispatch.asignacion_fallida", {
                "id_viaje": id_viaje,
                "id_pasajero": id_cliente,
                "motivo": "No hay conductores disponibles",
                "timestamp": data.get("fecha_solicitud")
            })
            return
        
        print(f"✅ [ASIGNADO] Conductor {resultado.id_conductor} asignado a viaje {id_viaje}")
        print(f"   - Algoritmo: {resultado.algoritmo_usado.value}")
        print(f"   - Tiempo asignación: {resultado.tiempo_asignacion_ms}ms")
        
        # 3. Confirmar asignación vía gRPC
        print(f"📡 Llamando a gRPC para confirmar asignación")
        
        grpc_response = reservas_grpc_client.confirmar_asignacion(
            id_viaje=id_viaje,
            id_conductor=resultado.id_conductor,
            metodo_asignacion="automatico",
            tiempo_asignacion_ms=resultado.tiempo_asignacion_ms,
            algoritmo_usado=resultado.algoritmo_usado.value
        )
        
        if grpc_response and grpc_response.get("success"):
            print(f"✅ [gRPC] Asignación confirmada en Reservas Service")
            
            # 4. Publicar evento de confirmación
            await publish_event("dispatch.asignacion_confirmada", {
                "id_viaje": id_viaje,
                "id_conductor": resultado.id_conductor,
                "id_pasajero": id_cliente,
                "algoritmo": resultado.algoritmo_usado.value,
                "tiempo_asignacion_ms": resultado.tiempo_asignacion_ms,
                "origen": origen,
                "destino": destino
            })
            
            print(f"✅ Evento 'dispatch.asignacion_confirmada' publicado")
        else:
            print(f"❌ [gRPC] Error confirmando asignación: {grpc_response}")
            
            # Revertir estado del conductor
            await users_client.actualizar_estado_conductor(
                id_conductor=resultado.id_conductor,
                estado="disponible"
            )
            
            await publish_event("dispatch.asignacion_fallida", {
                "id_viaje": id_viaje,
                "id_pasajero": id_cliente,
                "motivo": "Error confirmando con Reservas Service"
            })
    
    except ValueError as e:
        print(f"❌ [ERROR_VALIDACION] {e}")
        traceback.print_exc()
        await publish_event("dispatch.asignacion_fallida", {
            "id_viaje": id_viaje,
            "id_pasajero": id_cliente,
            "motivo": f"Datos inválidos: {str(e)}"
        })
    
    except Exception as e:
        print(f"❌ [ERROR_INTERNO] {e}")
        traceback.print_exc()
        
        await publish_event("dispatch.asignacion_fallida", {
            "id_viaje": id_viaje,
            "id_pasajero": id_cliente,
            "motivo": f"Error interno: {str(e)}"
        })
    
    finally:
        db.close()
        print("=" * 60)
        print("🏁 [HANDLER] handle_nueva_reserva FINALIZADO")
        print("=" * 60)


# NUEVO HANDLER
async def handle_viaje_completado(data: Dict[str, Any]):
    """
    Handler para evento: ride.viaje_completado
    
    Flujo:
    1. Recibe evento de viaje completado
    2. Extrae id_conductor
    3. Actualiza estado del conductor a 'disponible' vía Users Service
    """
    print("=" * 60)
    print("🎯 [HANDLER] handle_viaje_completado INICIADO")
    print("=" * 60)
    
    id_viaje = data.get('id_viaje')
    id_conductor = data.get('id_conductor')
    id_cliente = data.get('id_cliente')
    fecha_fin = data.get('fecha_fin')
    
    print(f"📦 Datos recibidos:")
    print(f"   - ID Viaje: {id_viaje}")
    print(f"   - ID Conductor: {id_conductor}")
    print(f"   - ID Cliente: {id_cliente}")
    print(f"   - Fecha Fin: {fecha_fin}")
    
    # Validar datos obligatorios
    if not id_conductor:
        print(f"❌ Error: No se proporcionó id_conductor")
        return
    
    try:
        # Liberar conductor (ocupado → disponible)
        print(f"🔄 [LIBERAR_CONDUCTOR] Actualizando conductor {id_conductor} a 'disponible'")
        
        actualizado = await users_client.actualizar_estado_conductor(
            id_conductor=id_conductor,
            estado="disponible"
        )
        
        if actualizado:
            print(f"✅ [LIBERAR_CONDUCTOR] Conductor {id_conductor} liberado exitosamente")
            
            # Publicar evento de confirmación (opcional)
            await publish_event("dispatch.conductor_liberado", {
                "id_conductor": id_conductor,
                "id_viaje": id_viaje,
                "motivo": "Viaje completado",
                "timestamp": fecha_fin
            })
        else:
            print(f"⚠️ [LIBERAR_CONDUCTOR] No se pudo actualizar estado del conductor {id_conductor}")
    
    except Exception as e:
        print(f"❌ [ERROR] Error liberando conductor {id_conductor}: {e}")
        traceback.print_exc()
    
    finally:
        print("=" * 60)
        print("🏁 [HANDLER] handle_viaje_completado FINALIZADO")
        print("=" * 60)