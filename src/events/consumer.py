import aio_pika
import aio_pika.exceptions
import json
import asyncio
import traceback

from src.config import settings
from src.events.handlers import handle_nueva_reserva, handle_viaje_completado


async def start_consumer():
    """Iniciar consumer de RabbitMQ"""
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            print(f"🐰 [CONSUMER] Iniciando consumer de RabbitMQ (intento {attempt + 1}/{max_retries})...")
            
            # Conectar a RabbitMQ
            connection = await aio_pika.connect_robust(
                settings.rabbitmq_url,
                timeout=10,
                heartbeat=60
            )
            
            print(f"✅ [CONSUMER] Conectado a RabbitMQ: {settings.rabbitmq_url}")
            
            # Crear canal
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=10)
            
            print(f"✅ [CONSUMER] Canal creado con QoS prefetch_count=10")
            
            # Declarar exchange
            exchange = await channel.declare_exchange(
                settings.rabbitmq_exchange,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            print(f"✅ [CONSUMER] Exchange declarado: {settings.rabbitmq_exchange}")
            
            # Declarar queue
            queue_name = "dispatch_queue"
            queue = await channel.declare_queue(
                queue_name,
                durable=True,
                arguments={
                    'x-message-ttl': 86400000,
                    'x-max-length': 10000
                }
            )
            
            print(f"✅ [CONSUMER] Queue declarada: {queue_name}")
            
            # : Binding para viaje completado
            routing_keys = [
                "ride.nueva_reserva",
                "ride.viaje_completado"  # ← NUEVO
            ]
            
            for routing_key in routing_keys:
                await queue.bind(exchange, routing_key=routing_key)
                print(f"🔗 [CONSUMER] Queue '{queue_name}' enlazada con routing key '{routing_key}'")
            
            #  CALLBACK DEL CONSUMER
            async def on_message(message: aio_pika.IncomingMessage):
                """Procesar mensaje recibido"""
                print("=" * 80)
                print(f"📨 [CONSUMER] ¡¡¡MENSAJE RECIBIDO!!!")
                print(f"   - Routing Key: {message.routing_key}")
                print(f"   - Content Type: {message.content_type}")
                print("=" * 80)
                
                async with message.process():
                    try:
                        # Decodificar mensaje
                        body_raw = message.body.decode('utf-8')
                        payload = json.loads(body_raw)
                        routing_key_received = message.routing_key
                        
                        print(f"📥 [CONSUMER] Payload parseado:")
                        print(json.dumps(payload, indent=2, ensure_ascii=False))
                        
                        # Despachar a handler
                        if routing_key_received == "ride.nueva_reserva":
                            print(f"🎯 [CONSUMER] Despachando a handle_nueva_reserva()")
                            await handle_nueva_reserva(payload)
                            print(f"✅ [CONSUMER] handle_nueva_reserva() completado")
                        
                        # : Handler para viaje completado
                        elif routing_key_received == "ride.viaje_completado":
                            print(f"🎯 [CONSUMER] Despachando a handle_viaje_completado()")
                            await handle_viaje_completado(payload)
                            print(f"✅ [CONSUMER] handle_viaje_completado() completado")
                        
                        else:
                            print(f"⚠️ [CONSUMER] Routing key no manejado: {routing_key_received}")
                        
                        print("=" * 80)
                    
                    except json.JSONDecodeError as e:
                        print(f"❌ [CONSUMER] Error JSON: {e}")
                        print(f"   Body problemático: {message.body}")
                        print("=" * 80)
                    
                    except Exception as e:
                        print(f"❌ [CONSUMER] Error procesando mensaje: {e}")
                        traceback.print_exc()
                        print("=" * 80)
            
            #  REGISTRAR CONSUMER
            consumer_tag = await queue.consume(
                on_message,
                no_ack=False
            )
            
            print(f"✅ [CONSUMER] Consumer registrado con tag: {consumer_tag}")
            print(f"👂 [CONSUMER] Escuchando mensajes en cola '{queue_name}'...")
            print(f"🔄 [CONSUMER] Loop infinito iniciado (esperando mensajes...)")
            
            # MANTENER VIVO EL CONSUMER INDEFINIDAMENTE
            await asyncio.Future()
        
        except aio_pika.exceptions.AMQPConnectionError as e:
            print(f"❌ [CONSUMER] Error de conexión AMQP: {e}")
            if attempt < max_retries - 1:
                print(f"🔄 [CONSUMER] Reintentando en {retry_delay} segundos...")
                await asyncio.sleep(retry_delay)
            else:
                print(f"❌ [CONSUMER] Máximo de reintentos alcanzado")
                raise
        
        except Exception as e:
            print(f"❌ [CONSUMER] Error inesperado: {e}")
            traceback.print_exc()
            if attempt < max_retries - 1:
                print(f"🔄 [CONSUMER] Reintentando en {retry_delay} segundos...")
                await asyncio.sleep(retry_delay)
            else:
                print(f"❌ [CONSUMER] Error fatal, terminando")
                raise