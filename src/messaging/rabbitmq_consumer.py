import pika
import json
import time
from typing import Callable
from src.config import settings
from src.database import SessionLocal
from src.services.asignacion_service import AsignacionService
from src.schemas.asignacion import AsignacionCreate
from src.models.asignacion import TipoAlgoritmo
from src.utils.logger import logger
from src.messaging.rabbitmq_publisher import RabbitMQPublisher


class RabbitMQConsumer:
    """Consumidor de mensajes de RabbitMQ"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.publisher = RabbitMQPublisher()
        self._connect()
    
    def _connect(self):
        """Establecer conexión con RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(
                settings.rabbitmq_user,
                settings.rabbitmq_password
            )
            
            parameters = pika.ConnectionParameters(
                host=settings.rabbitmq_host,
                port=settings.rabbitmq_port,
                virtual_host=settings.rabbitmq_vhost,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declarar exchange
            self.channel.exchange_declare(
                exchange=settings.rabbitmq_exchange,
                exchange_type='topic',
                durable=True
            )
            
            # Declarar cola de nuevas reservas
            self.channel.queue_declare(
                queue=settings.rabbitmq_queue_nuevas_reservas,
                durable=True
            )
            
            # Bindear cola a exchange
            self.channel.queue_bind(
                exchange=settings.rabbitmq_exchange,
                queue=settings.rabbitmq_queue_nuevas_reservas,
                routing_key='reserva.nueva'
            )
            
            # Configurar QoS
            self.channel.basic_qos(prefetch_count=1)
            
            logger.info("Conectado a RabbitMQ exitosamente")
            
        except Exception as e:
            logger.error(f"Error conectando a RabbitMQ: {str(e)}")
            raise
    
    def _procesar_nueva_reserva(self, ch, method, properties, body):
        """Callback para procesar nuevas reservas"""
        db = SessionLocal()
        
        try:
            # Parsear mensaje
            mensaje = json.loads(body.decode('utf-8'))
            logger.info(f"Mensaje recibido: {mensaje}")
            
            # Validar estructura del mensaje
            required_fields = ['id_viaje', 'id_pasajero', 'origen', 'destino']
            if not all(field in mensaje for field in required_fields):
                logger.error(f"Mensaje con estructura inválida: {mensaje}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            
            # Crear asignación automática
            asignacion_data = AsignacionCreate(
                id_viaje=mensaje['id_viaje'],
                id_pasajero=mensaje['id_pasajero'],
                origen=mensaje['origen'],
                destino=mensaje['destino'],
                prioridad=mensaje.get('prioridad', 1)
            )
            
            # Determinar algoritmo
            algoritmo = TipoAlgoritmo.ROUND_ROBIN
            if 'algoritmo' in mensaje:
                algoritmo_map = {
                    'round_robin': TipoAlgoritmo.ROUND_ROBIN,
                    'calificacion': TipoAlgoritmo.CALIFICACION,
                    'cercania': TipoAlgoritmo.CERCANIA,
                    'menor_carga': TipoAlgoritmo.MENOR_CARGA
                }
                algoritmo = algoritmo_map.get(
                    mensaje['algoritmo'].lower(),
                    TipoAlgoritmo.ROUND_ROBIN
                )
            
            # Intentar asignación
            asignacion = AsignacionService.crear_asignacion_automatica(
                db, asignacion_data, algoritmo
            )
            
            if asignacion:
                # Publicar evento de asignación exitosa
                from src.models.conductor import Conductor
                conductor = db.query(Conductor).filter(
                    Conductor.id_conductor == asignacion.id_conductor
                ).first()
                
                evento = {
                    "evento": "viaje_asignado",
                    "id_viaje": asignacion.id_viaje,
                    "id_asignacion": asignacion.id_asignacion,
                    "id_conductor": asignacion.id_conductor,
                    "id_pasajero": asignacion.id_pasajero,
                    "conductor": {
                        "nombre": conductor.nombre_completo,
                        "placa": conductor.placa_auto,
                        "modelo": conductor.modelo_auto,
                        "calificacion": conductor.calificacion_promedio
                    },
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                self.publisher.publicar_asignacion(evento)
                
                logger.info(
                    f"Asignación exitosa - Viaje: {asignacion.id_viaje}, "
                    f"Conductor: {asignacion.id_conductor}"
                )
            else:
                logger.warning(
                    f"No se pudo asignar conductor para viaje {mensaje['id_viaje']}"
                )
                
                # Publicar evento de asignación fallida
                evento_fallo = {
                    "evento": "asignacion_fallida",
                    "id_viaje": mensaje['id_viaje'],
                    "motivo": "No hay conductores disponibles",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                self.publisher.publicar_asignacion(evento_fallo)
            
            # Confirmar procesamiento
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON: {str(e)}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        
        except Exception as e:
            logger.error(f"Error procesando reserva: {str(e)}")
            # Rechazar mensaje y reencolar
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        finally:
            db.close()
    
    def iniciar_consumo(self):
        """Iniciar consumo de mensajes"""
        try:
            logger.info(
                f"Esperando mensajes en cola '{settings.rabbitmq_queue_nuevas_reservas}'..."
            )
            
            self.channel.basic_consume(
                queue=settings.rabbitmq_queue_nuevas_reservas,
                on_message_callback=self._procesar_nueva_reserva,
                auto_ack=False
            )
            
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("Consumidor detenido por el usuario")
            self.detener()
        except Exception as e:
            logger.error(f"Error en el consumidor: {str(e)}")
            self.detener()
            raise
    
    def detener(self):
        """Detener el consumidor y cerrar conexiones"""
        try:
            if self.channel and self.channel.is_open:
                self.channel.stop_consuming()
                self.channel.close()
            
            if self.connection and self.connection.is_open:
                self.connection.close()
            
            self.publisher.cerrar()
            
            logger.info("Consumidor RabbitMQ detenido")
        except Exception as e:
            logger.error(f"Error al detener consumidor: {str(e)}")


def main():
    """Función principal para ejecutar el consumidor"""
    consumer = RabbitMQConsumer()
    try:
        consumer.iniciar_consumo()
    except Exception as e:
        logger.error(f"Error fatal: {str(e)}")
        consumer.detener()


if __name__ == "__main__":
    main()