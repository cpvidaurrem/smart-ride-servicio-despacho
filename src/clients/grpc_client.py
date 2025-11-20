import grpc
from typing import Optional, Dict, Any
import sys
import os

#  Añadir /app/src/generated al PYTHONPATH
GENERATED_PATH = os.path.join(os.path.dirname(__file__), '..', 'generated')
if GENERATED_PATH not in sys.path:
    sys.path.insert(0, GENERATED_PATH)

from src.config import settings

try:
    import reservas_pb2
    import reservas_pb2_grpc
    print("✅ Proto files importados correctamente")
except ImportError as e:
    print(f"❌ Error importando proto files: {e}")
    print(f"   PYTHONPATH: {sys.path}")
    print(f"   Archivos en generated: {os.listdir(GENERATED_PATH) if os.path.exists(GENERATED_PATH) else 'No existe'}")
    reservas_pb2 = None
    reservas_pb2_grpc = None


class ReservasGrpcClient:
    """Cliente gRPC para Reservas Service"""
    
    def __init__(self):
        self.channel = None
        self.stub = None
        self.grpc_url = settings.reservas_grpc_url
        print(f"🔧 gRPC Client inicializado - URL: {self.grpc_url}")
    
    def connect(self):
        """Conectar al servidor gRPC"""
        if not reservas_pb2 or not reservas_pb2_grpc:
            print("❌ Proto files no disponibles - no se puede conectar")
            return False
        
        try:
            print(f"🔌 Conectando a gRPC: {self.grpc_url}")
            self.channel = grpc.insecure_channel(
                self.grpc_url,
                options=[
                    ('grpc.max_send_message_length', 50 * 1024 * 1024),
                    ('grpc.max_receive_message_length', 50 * 1024 * 1024),
                    ('grpc.keepalive_time_ms', 30000),
                ]
            )
            self.stub = reservas_pb2_grpc.ReservasServiceStub(self.channel)
            print(f"✅ Conectado a gRPC: {self.grpc_url}")
            return True
        except Exception as e:
            print(f"❌ Error conectando a gRPC: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def confirmar_asignacion(
        self,
        id_viaje: int,
        id_conductor: int,
        metodo_asignacion: str = "automatico",
        tiempo_asignacion_ms: int = 0,
        algoritmo_usado: str = "calificacion"
    ) -> Optional[Dict[str, Any]]:
        """Confirmar asignación vía gRPC"""
        if not self.stub:
            print("⚠️ Stub no inicializado, conectando...")
            if not self.connect():
                return None
        
        try:
            request = reservas_pb2.ConfirmarAsignacionRequest(
                id_viaje=id_viaje,
                id_conductor=id_conductor,
                metodo_asignacion=metodo_asignacion,
                tiempo_asignacion_ms=tiempo_asignacion_ms,
                algoritmo_usado=algoritmo_usado
            )
            
            print(f"📤 [gRPC] Enviando ConfirmarAsignacion:")
            print(f"   - Viaje: {id_viaje}")
            print(f"   - Conductor: {id_conductor}")
            print(f"   - Método: {metodo_asignacion}")
            print(f"   - Algoritmo: {algoritmo_usado}")
            
            response = self.stub.ConfirmarAsignacion(request, timeout=10)
            
            print(f"✅ [gRPC] Respuesta recibida: {response.message}")
            
            return {
                "success": response.success,
                "message": response.message,
                "viaje": {
                    "id_viaje": response.viaje.id_viaje,
                    "id_cliente": response.viaje.id_cliente,
                    "id_conductor": response.viaje.id_conductor,
                    "origen": response.viaje.origen,
                    "destino": response.viaje.destino,
                    "estado": response.viaje.estado,
                } if response.viaje else None
            }
        
        except grpc.RpcError as e:
            print(f"❌ [gRPC] Error RPC: [{e.code().name}] {e.details()}")
            return {
                "success": False,
                "message": f"Error gRPC: {e.details()}"
            }
        except Exception as e:
            print(f"❌ [gRPC] Error inesperado: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def close(self):
        """Cerrar canal"""
        if self.channel:
            self.channel.close()
            print("✅ Canal gRPC cerrado")


# Instancia global
reservas_grpc_client = ReservasGrpcClient()