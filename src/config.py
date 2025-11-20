from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Aplicación
    app_name: str = "Servicio de Despacho - Smart Ride"
    app_version: str = "1.0.0"
    environment: str = "production"
    debug: bool = True
    port: int = 8003
    
    # Base de datos
    database_url: str = "postgresql://usuario:usuario123@postgres-despacho:5432/db_smartride_despacho"
    db_host: str = "postgres-despacho"
    db_port: int = 5432
    db_name: str = "db_smartride_despacho"
    db_user: str = "usuario"
    db_password: str = "usuario123"
    
    # RabbitMQ
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672"
    rabbitmq_exchange: str = "smart_ride_exchange"
    
    # Servicios externos
    users_service_url: str = "http://users-service:3001"
    reservas_service_url: str = "http://reservas-service:3002"
    
    # gRPC
    reservas_grpc_url: str = "reservas-service:50051"
    
    # JWT
    jwt_secret: str = "3583fbebc94b3a65b11d63e791f49e7de5e4b8bde1bb8548e707f1a78f321c6118f3aa0edf7d1c1429bb199979241ad30a8447acc27c085a89148647b254f402"
    
    # Logs
    log_level: str = "INFO"
    log_format: str = "json"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()