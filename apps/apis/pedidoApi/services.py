"""
Servicios de negocio para la API de Pedidos.
"""
import logging
from decimal import Decimal
from typing import Optional

from django.db import transaction

from .models import MetodoEnvio

logger = logging.getLogger(__name__)


def obtener_o_crear_metodo_envio_defecto() -> MetodoEnvio:
    """
    Obtiene el primer método de envío activo disponible.
    Si no existe ninguno, crea automáticamente un "Envío estándar" con valores por defecto.
    
    Esta función es robusta y se ejecuta sin errores incluso si la BD está vacía o recién inicializada.
    
    Returns:
        MetodoEnvio: El método de envío a utilizar.
        
    Raises:
        No levanta excepciones. En el peor caso, crea y retorna un método por defecto.
    """
    try:
        # Intentar obtener el primer método activo
        metodo = MetodoEnvio.objects.filter(activo=True).first()
        
        if metodo:
            logger.info(f"Método de envío obtenido: {metodo.nombre} (tipo: {metodo.tipo_transporte})")
            return metodo
        
        logger.warning("No hay métodos de envío activos en la BD. Creando método por defecto.")
        
        # Si no existe ninguno, crear el método estándar por defecto
        with transaction.atomic():
            metodo_defecto, created = MetodoEnvio.objects.get_or_create(
                tipo_transporte="road",
                defaults={
                    "nombre": "Envío estándar",
                    "descripcion": "Envío estándar a domicilio (2-5 días hábiles)",
                    "costo": Decimal("0.00"),
                    "dias_estimados": "2-5",
                    "activo": True,
                }
            )
            
            if created:
                logger.info(f"Método de envío por defecto creado: {metodo_defecto.nombre}")
            else:
                logger.info(f"Método de envío por defecto ya existía: {metodo_defecto.nombre}")
            
            return metodo_defecto
            
    except Exception as e:
        logger.exception(f"Error obteniendo o creando método de envío: {e}")
        # En caso de error inesperado, intentar una última vez con get_or_create simple
        try:
            metodo, _ = MetodoEnvio.objects.get_or_create(
                tipo_transporte="road",
                defaults={
                    "nombre": "Envío estándar",
                    "descripcion": "Envío estándar a domicilio",
                    "costo": Decimal("0.00"),
                    "dias_estimados": "2-5",
                    "activo": True,
                }
            )
            return metodo
        except Exception as e2:
            logger.error(f"Error crítico creando método de envío: {e2}")
            raise


def obtener_metodo_envio_por_tipo(tipo_transporte: str) -> Optional[MetodoEnvio]:
    """
    Obtiene un método de envío específico por su tipo de transporte.
    Si no existe o no está activo, retorna None.
    
    Args:
        tipo_transporte: El tipo de transporte (p.ej. 'road', 'air', 'sea', 'rail', 'domicilio', 'demo_tracking').
        
    Returns:
        MetodoEnvio o None si no existe.
    """
    try:
        return MetodoEnvio.objects.filter(
            tipo_transporte=tipo_transporte,
            activo=True
        ).first()
    except Exception as e:
        logger.exception(f"Error obteniendo método de envío {tipo_transporte}: {e}")
        return None


def obtener_metodo_envio_seguro(tipo_transporte: Optional[str] = None) -> MetodoEnvio:
    """
    Obtiene de forma segura un método de envío.
    
    1. Si tipo_transporte es proporcionado y existe un método activo con ese tipo, lo retorna.
    2. Si no, obtiene el primer método activo disponible.
    3. Si no hay métodos activos, crea y retorna el método por defecto.
    
    Esta función nunca levanta excepciones.
    
    Args:
        tipo_transporte: Opcional, el tipo de transporte preferido.
        
    Returns:
        MetodoEnvio: Un método de envío garantizado de estar disponible.
    """
    # Si se proporciona un tipo, intentar obtenerlo
    if tipo_transporte:
        metodo = obtener_metodo_envio_por_tipo(tipo_transporte)
        if metodo:
            logger.info(f"Método de envío {tipo_transporte} obtenido")
            return metodo
        logger.warning(f"Tipo de transporte {tipo_transporte} no disponible. Usando método por defecto.")
    
    # Si no hay tipo o no existe, obtener el por defecto
    return obtener_o_crear_metodo_envio_defecto()
