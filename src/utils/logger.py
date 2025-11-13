import logging
import sys
from pythonjsonlogger import jsonlogger
from src.config import settings


def setup_logger(name: str) -> logging.Logger:
    """
    Configurar logger con formato JSON para ambientes de producción
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Evitar duplicación de logs
    if logger.hasHandlers():
        logger.handlers.clear()
    
    handler = logging.StreamHandler(sys.stdout)
    
    if settings.log_format == "json":
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


# Logger principal del servicio
logger = setup_logger("servicio_despacho")