from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Aplicación
    app_name: str = "Servicio de Despacho - Smart Ride"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    port: int = 8003
    
    # Base de datos (configurado para Docker)
    database_url: str = "postgresql://despacho_user:despacho_pass@postgres:5432/despacho_db"
    db_host: str = "postgres"
    db_port: int = 5432
    db_name: str = "despacho_db"
    db_user: str = "despacho_user"
    db_password: str = "despacho_pass"
    
    # RabbitMQ (configurado para Docker)
    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_vhost: str = "/"
    rabbitmq_queue_nuevas_reservas: str = "nueva_reserva"
    rabbitmq_queue_asignaciones: str = "viaje_asignado"
    rabbitmq_exchange: str = "smart_ride_exchange"
    
    # gRPC
    grpc_host: str = "0.0.0.0"
    grpc_port: int = 50051
    
    # Redis (configurado para Docker)
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Logs
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Servicios externos (configurado para Docker)
    ride_service_grpc_host: str = "servicio-viajes"
    ride_service_grpc_port: int = 50052
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()