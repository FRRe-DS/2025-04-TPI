"""Cliente HTTP especializado para la API de pedidos.

Este módulo define :class:`PedidoAPIClient`, una clase que hereda del
cliente base ubicado en ``utils.apiCliente.base``. El objetivo es
mantener un único punto de integración con la API REST de pedidos que
exponemos en este proyecto. De esta forma, cuando se re-direccione el
tráfico hacia otra implementación compatible, solo será necesario
ajustar la configuración del ``base_url`` sin tocar el resto del código
que consume estos servicios.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from django.conf import settings

from utils.apiCliente.base import BaseAPIClient
from utils.apiCliente.logistica import LogisticsClient
from utils.apiCliente.stock import StockClient


class PedidoAPIClient(BaseAPIClient):
    """Cliente concreto para interactuar con la API de pedidos.

    El contrato implementado por este cliente está alineado con el
    ``PedidoViewSet`` definido en ``apps.apis.pedidoApi.views``. Por lo
    tanto, los métodos expuestos se corresponden con los endpoints
    disponibles en la API interna:

    - ``GET    /pedidos/``                        → :meth:`listar_pedidos`
    - ``POST   /pedidos/``                        → :meth:`crear_pedido`
    - ``GET    /pedidos/{pedido_id}/``            → :meth:`obtener_pedido`
    - ``POST   /pedidos/{pedido_id}/confirmar/``  → :meth:`confirmar_pedido`
    - ``DELETE /pedidos/{pedido_id}/cancelar/``   → :meth:`cancelar_pedido`
    - ``GET    /pedidos/history/``                → :meth:`history`
    - ``GET    /pedidos/{pedido_id}/history-detail/`` → :meth:`history_detail`
    - ``POST   /pedidos/{pedido_id}/tracking/``   → :meth:`crear_tracking`
    - ``GET    /pedidos/{pedido_id}/tracking/``   → :meth:`obtener_tracking`

    Parameters
    ----------
    base_url:
        URL base del servicio. Si no se indica se utiliza la
        configuración del proyecto.
    timeout:
        Tiempo máximo de espera por respuesta HTTP.
    max_retries:
        Número máximo de reintentos ante errores de conexión o timeout.
    token / api_key:
        Credenciales opcionales para enviar en cada request.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        *,
        timeout: float = 8.0,
        max_retries: int = 2,
        token: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        base_por_defecto = getattr(settings, "base_url_api", "http://localhost:8000/api/")
        if base_url is None:
            base_url = getattr(settings, "PEDIDOS_API_BASE_URL", base_por_defecto) or base_por_defecto

        super().__init__(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            token=token,
            api_key=api_key,
        )

    # ------------------------------------------------------------------
    # Endpoints principales de la API de pedidos
    # ------------------------------------------------------------------

    def obtener_pedido(self, pedido_id: int) -> Any:
        """Obtiene el detalle de un pedido específico."""
        return self.get(f"/pedidos/{pedido_id}/", expected_status=200)

    def crear_pedido(
        self,
        *,
        direccion_envio: Dict[str, Any],
        detalles: Iterable[Dict[str, Any]],
        tipo_transporte: Optional[str] = None,
    ) -> Any:
        """Crea un nuevo pedido en la API interna."""
        payload: Dict[str, Any] = {
            "direccion_envio": direccion_envio,
            "detalles": list(detalles),
        }
        if tipo_transporte:
            payload["tipo_transporte"] = tipo_transporte

        return self.post("/pedidos/", json=payload, expected_status=201)

    def confirmar_pedido(self, pedido_id: int, *, tipo_transporte: Optional[str] = None) -> Any:
        """Confirma un pedido, activando el flujo de logística y stock."""
        payload: Dict[str, Any] = {}
        if tipo_transporte:
            payload["tipo_transporte"] = tipo_transporte
        return self.post(
            f"/pedidos/{pedido_id}/confirmar/",
            json=payload or None,
            expected_status=200,
        )

    def cancelar_pedido(self, pedido_id: int) -> Any:
        """Cancela un pedido específico."""
        return self.delete(f"/pedidos/{pedido_id}/cancelar/", expected_status=200)

    def history(self, **params: Any) -> Any:
        """Lista el historial de pedidos del usuario autenticado.
        
        Corresponde a GET /api/shopcart/history
        """
        return self.get("/pedidos/history/", params=params or None, expected_status=200)

    def history_detail(self, pedido_id: int) -> Any:
        """Obtiene el detalle de un pedido específico del historial.
        
        Corresponde a GET /api/shopcart/history/{id}
        """
        return self.get(f"/pedidos/{pedido_id}/history-detail/", expected_status=200)

    def crear_tracking(self, pedido_id: int, *, tipo_transporte: Optional[str] = None) -> Any:
        """Crea y vincula un tracking de logística al pedido dado.

        Envía un POST a ``/pedidos/{id}/tracking/``. Si ``tipo_transporte`` se
        especifica, se incluye en el cuerpo; de lo contrario, el backend usará
        el previamente definido en el pedido.
        
        Corresponde a POST /api/pedidos/{id}/tracking/
        """
        payload: Dict[str, Any] = {}
        if tipo_transporte:
            payload["tipo_transporte"] = tipo_transporte
        return self.post(
            f"/pedidos/{pedido_id}/tracking/",
            json=payload or None,
            expected_status=201,
        )

    def obtener_tracking(self, pedido_id: int) -> Any:
        """Obtiene el tracking asociado a un pedido.

        Realiza un GET a ``/pedidos/{id}/tracking/``.
        
        Corresponde a GET /api/pedidos/{id}/tracking/
        """
        return self.get(f"/pedidos/{pedido_id}/tracking/", expected_status=200)


def obtener_cliente_pedidos(**kwargs: Any) -> PedidoAPIClient:
    """Helper para instanciar ``PedidoAPIClient`` usando la configuración del proyecto."""
    base_por_defecto = getattr(settings, "base_url_api", "http://localhost:8000/api/")
    base_url = getattr(settings, "PEDIDOS_API_BASE_URL", base_por_defecto) or base_por_defecto
    return PedidoAPIClient(base_url=base_url, **kwargs)


def obtener_cliente_logistica() -> LogisticsClient:
    base_por_defecto = getattr(settings, "base_url_api", "http://localhost:8000/api/")
    base_url = getattr(settings, "LOGISTICS_API_BASE_URL", base_por_defecto) or base_por_defecto
    return LogisticsClient(base_url=base_url)


def obtener_cliente_stock() -> StockClient:
    base_por_defecto = getattr(settings, "base_url_api", "http://localhost:8000/api/")
    base_url = getattr(settings, "STOCK_API_BASE_URL", base_por_defecto) or base_por_defecto
    return StockClient(base_url=base_url)
