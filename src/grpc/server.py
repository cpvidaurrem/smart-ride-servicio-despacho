import grpc
from concurrent import futures
import sys
import os

# Añadir path para imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.grpc import despacho_pb2, despacho_pb2_grpc
from src.database import SessionLocal
from src.services.asignacion_service import AsignacionService
from src.schemas.asignacion import AsignacionCreate
from src.models.asignacion import TipoAlgoritmo, EstadoAsignacion
from src.utils.logger import logger
from src.config import settings


class DespachoServicer(despacho_pb2_grpc.DespachoServiceServicer):
    """Implementación del servicio gRPC de Despacho"""
    
    def ConfirmarAsignacion(self, request, context):
        """Confirmar asignación de conductor a un viaje"""
        db = SessionLocal()
        
        try:
            logger.info(f"gRPC: Recibida solicitud de asignación para viaje {request.id_viaje}")
            
            # Mapear algoritmo
            algoritmo_map = {
                "round_robin": TipoAlgoritmo.ROUND_ROBIN,
                "calificacion": TipoAlgoritmo.CALIFICACION,
                "cercania": TipoAlgoritmo.CERCANIA,
                "menor_carga": TipoAlgoritmo.MENOR_CARGA
            }
            algoritmo = algoritmo_map.get(
                request.algoritmo.lower(),
                TipoAlgoritmo.ROUND_ROBIN
            )
            
            # Crear asignación
            asignacion_data = AsignacionCreate(
                id_viaje=request.id_viaje,
                id_pasajero=request.id_pasajero,
                origen=request.origen,
                destino=request.destino,
                prioridad=request.prioridad if request.prioridad > 0 else 1
            )
            
            asignacion = AsignacionService.crear_asignacion_automatica(
                db, asignacion_data, algoritmo
            )
            
            if not asignacion:
                return despacho_pb2.AsignacionResponse(
                    exito=False,
                    mensaje="No hay conductores disponibles",
                    id_asignacion=0,
                    tiempo_asignacion_ms=0
                )
            
            # Obtener información del conductor
            conductor = db.query(
                __import__('src.models.conductor', fromlist=['Conductor']).Conductor
            ).filter_by(id_conductor=asignacion.id_conductor).first()
            
            conductor_info = despacho_pb2.ConductorInfo(
                id_conductor=conductor.id_conductor,
                nombre_completo=conductor.nombre_completo,
                modelo_auto=conductor.modelo_auto,
                placa_auto=conductor.placa_auto,
                calificacion=conductor.calificacion_promedio,
                ubicacion_lat=conductor.ubicacion_lat or 0.0,
                ubicacion_lng=conductor.ubicacion_lng or 0.0
            )
            
            logger.info(
                f"gRPC: Asignación exitosa - viaje={request.id_viaje}, "
                f"conductor={conductor.id_conductor}"
            )
            
            return despacho_pb2.AsignacionResponse(
                exito=True,
                mensaje="Conductor asignado exitosamente",
                id_asignacion=asignacion.id_asignacion,
                conductor=conductor_info,
                tiempo_asignacion_ms=asignacion.tiempo_asignacion_ms or 0
            )
            
        except Exception as e:
            logger.error(f"gRPC: Error en ConfirmarAsignacion: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error interno: {str(e)}")
            return despacho_pb2.AsignacionResponse(
                exito=False,
                mensaje=f"Error: {str(e)}",
                id_asignacion=0,
                tiempo_asignacion_ms=0
            )
        finally:
            db.close()
    
    def ObtenerConductorAsignado(self, request, context):
        """Obtener el conductor asignado a un viaje"""
        db = SessionLocal()
        
        try:
            asignacion = AsignacionService.obtener_asignacion_por_viaje(
                db, request.id_viaje
            )
            
            if not asignacion:
                return despacho_pb2.ConductorResponse(
                    encontrado=False,
                    estado_asignacion="no_encontrado"
                )
            
            conductor = db.query(
                __import__('src.models.conductor', fromlist=['Conductor']).Conductor
            ).filter_by(id_conductor=asignacion.id_conductor).first()
            
            conductor_info = despacho_pb2.ConductorInfo(
                id_conductor=conductor.id_conductor,
                nombre_completo=conductor.nombre_completo,
                modelo_auto=conductor.modelo_auto,
                placa_auto=conductor.placa_auto,
                calificacion=conductor.calificacion_promedio,
                ubicacion_lat=conductor.ubicacion_lat or 0.0,
                ubicacion_lng=conductor.ubicacion_lng or 0.0
            )
            
            return despacho_pb2.ConductorResponse(
                encontrado=True,
                conductor=conductor_info,
                estado_asignacion=asignacion.estado.value
            )
            
        except Exception as e:
            logger.error(f"gRPC: Error en ObtenerConductorAsignado: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return despacho_pb2.ConductorResponse(encontrado=False)
        finally:
            db.close()
    
    def CancelarAsignacion(self, request, context):
        """Cancelar una asignación existente"""
        db = SessionLocal()
        
        try:
            asignacion = AsignacionService.obtener_asignacion_por_viaje(
                db, request.id_viaje
            )
            
            if not asignacion:
                return despacho_pb2.CancelacionResponse(
                    exito=False,
                    mensaje="Asignación no encontrada"
                )
            
            from src.schemas.asignacion import AsignacionUpdate
            AsignacionService.actualizar_asignacion(
                db,
                asignacion.id_asignacion,
                AsignacionUpdate(
                    estado=EstadoAsignacion.CANCELADO,
                    motivo_rechazo=request.motivo
                )
            )
            
            logger.info(f"gRPC: Asignación cancelada para viaje {request.id_viaje}")
            
            return despacho_pb2.CancelacionResponse(
                exito=True,
                mensaje="Asignación cancelada exitosamente"
            )
            
        except Exception as e:
            logger.error(f"gRPC: Error en CancelarAsignacion: {str(e)}")
            return despacho_pb2.CancelacionResponse(
                exito=False,
                mensaje=f"Error: {str(e)}"
            )
        finally:
            db.close()
    
    def VerificarDisponibilidad(self, request, context):
        """Verificar disponibilidad de conductores"""
        db = SessionLocal()
        
        try:
            from src.services.conductor_service import ConductorService
            conductores = ConductorService.obtener_conductores_disponibles(db)
            
            cantidad = len(conductores)
            
            return despacho_pb2.DisponibilidadResponse(
                conductores_disponibles=cantidad,
                hay_disponibilidad=cantidad > 0
            )
            
        except Exception as e:
            logger.error(f"gRPC: Error en VerificarDisponibilidad: {str(e)}")
            return despacho_pb2.DisponibilidadResponse(
                conductores_disponibles=0,
                hay_disponibilidad=False
            )
        finally:
            db.close()


def serve():
    """Iniciar servidor gRPC"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    despacho_pb2_grpc.add_DespachoServiceServicer_to_server(
        DespachoServicer(), server
    )
    
    address = f"{settings.grpc_host}:{settings.grpc_port}"
    server.add_insecure_port(address)
    
    logger.info(f"Servidor gRPC iniciado en {address}")
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()