import pika
import json
from src.config import settings
from src.utils.logger import logger


class RabbitMQPublisher:
    """Publicador de mensajes a RabbitMQ"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
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
            
            # Declarar cola de asignaciones
            self.channel.queue_declare(
                queue=settings.rabbitmq_queue_asignaciones,
                durable=True
            )
            
            # Bindear cola a exchange
            self.channel.queue_bind(
                exchange=settings.rabbitmq_exchange,
                queue=settings.rabbitmq_queue_asignaciones,
                routing_key='viaje.asignado'
            )
            
            logger.info("Publisher conectado a RabbitMQ")
            
        except Exception as e:
            logger.error(f"Error conectando publisher a RabbitMQ: {str(e)}")
            raise
    
    def publicar_asignacion(self, mensaje: dict):
        """
        Publicar un mensaje de asignación exitosa
        """
        try:
            # Asegurar que la conexión está activa
            if not self.connection or self.connection.is_closed:
                self._connect()
            
            mensaje_json = json.dumps(mensaje, ensure_ascii=False)
            
            self.channel.basic_publish(
                exchange=settings.rabbitmq_exchange,
                routing_key='viaje.asignado',
                body=mensaje_json,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Mensaje persistente
                    content_type='application/json'
                )
            )
            
            logger.info(f"Mensaje publicado: {mensaje.get('evento', 'evento_desconocido')}")
            
        except Exception as e:
            logger.error(f"Error publicando mensaje: {str(e)}")
            # Intentar reconectar
            try:
                self._connect()
            except:
                pass
    
    def publicar_evento(self, routing_key: str, mensaje: dict):
        """
        Publicar un evento genérico con routing key personalizado
        """
        try:
            if not self.connection or self.connection.is_closed:
                self._connect()
            
            mensaje_json = json.dumps(mensaje, ensure_ascii=False)
            
            self.channel.basic_publish(
                exchange=settings.rabbitmq_exchange,
                routing_key=routing_key,
                body=mensaje_json,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )
            
            logger.info(f"Evento publicado con routing_key: {routing_key}")
            
        except Exception as e:
            logger.error(f"Error publicando evento: {str(e)}")
    
    def cerrar(self):
        """Cerrar conexiones"""
        try:
            if self.channel and self.channel.is_open:
                self.channel.close()
            
            if self.connection and self.connection.is_open:
                self.connection.close()
            
            logger.info("Publisher cerrado")
        except Exception as e:
            logger.error(f"Error cerrando publisher: {str(e)}")