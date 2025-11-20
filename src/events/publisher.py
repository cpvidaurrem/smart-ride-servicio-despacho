import aio_pika
import json
from typing import Dict, Any, Optional
from src.config import settings

# Variables globales
_connection: Optional[aio_pika.RobustConnection] = None
_channel: Optional[aio_pika.Channel] = None
_exchange: Optional[aio_pika.Exchange] = None


async def init_rabbitmq() -> bool:
    """Inicializar conexión a RabbitMQ"""
    global _connection, _channel, _exchange
    
    try:
        print(f"🐰 Conectando a RabbitMQ: {settings.rabbitmq_url}")
        
        # Crear conexión robusta
        _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        
        # Crear canal
        _channel = await _connection.channel()
        
        # Declarar exchange
        _exchange = await _channel.declare_exchange(
            settings.rabbitmq_exchange,
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        
        print(f"✅ RabbitMQ inicializado - Exchange: {settings.rabbitmq_exchange}")
        return True
    except Exception as e:
        print(f"❌ Error conectando a RabbitMQ: {e}")
        return False


async def publish_event(routing_key: str, payload: Dict[str, Any]) -> bool:
    """
    Publicar evento a RabbitMQ
    
    Args:
        routing_key: Clave de enrutamiento (ej: 'dispatch.asignacion_confirmada')
        payload: Datos del evento
    """
    global _exchange
    
    if not _exchange:
        print("⚠️ RabbitMQ no inicializado")
        return False
    
    try:
        message = aio_pika.Message(
            body=json.dumps(payload, default=str).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        
        await _exchange.publish(
            message,
            routing_key=routing_key
        )
        
        print(f"📤 Evento publicado: {routing_key}")
        return True
    except Exception as e:
        print(f"❌ Error publicando evento: {e}")
        return False


async def close_rabbitmq():
    """Cerrar conexión a RabbitMQ"""
    global _connection
    
    if _connection and not _connection.is_closed:
        await _connection.close()
        print("✅ Conexión RabbitMQ cerrada")