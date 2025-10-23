"""Cliente HTTP para interactuar con el servicio de carrito (aCarrito).

Este módulo expone una clase especializada que hereda del cliente base
ubicado en ``utils.apiCliente``. La clase encapsula todas las
operaciones que ofrece la API de carrito, de forma que el resto del
código de Django pueda permanecer desacoplado de los detalles de
comunicación HTTP. El objetivo es que, cuando se redirija el tráfico
hacia otra implementación compatible de la API, el cambio se limite a la
configuración del ``base_url`` sin tener que ajustar las vistas ni los
serializadores.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from django.conf import settings

from utils.apiCliente.base import BaseAPIClient
from utils.apiCliente.stock import StockClient


class CarritoAPIClient(BaseAPIClient):
    """Cliente concreto para la API de carrito (aCarrito).

    El contrato que implementa este cliente está basado en el conjunto de
    endpoints expuestos por nuestra API interna de carrito:

    - ``GET    /shopcart/``               → :meth:`obtener_carrito`
    - ``POST   /shopcart/``               → :meth:`agregar_producto`
    - ``PUT    /shopcart/{productId}/``   → :meth:`actualizar_producto`
    - ``DELETE /shopcart/{productId}/``   → :meth:`eliminar_producto`
    - ``DELETE /shopcart/``               → :meth:`vaciar_carrito`
    - ``PUT    /shopcart/``               → :meth:`sincronizar_carrito`

    Además, se exponen utilidades para recuperar información de los
    productos asociados al carrito reutilizando el ``StockClient``.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        *,
        timeout: float = 8.0,
        max_retries: int = 2,
        token: Optional[str] = None,
        api_key: Optional[str] = None,
        stock_client: Optional[StockClient] = None,
    ) -> None:
        # establecer URL base por defecto desde la configuración de Django (setting estimado setting)
        base_por_defecto = getattr(settings, "base_url_api", "http://localhost:8000/api/")
        if base_url is None:
            base_url = getattr(settings, "CARRITO_API_BASE_URL", base_por_defecto) or base_por_defecto

        super().__init__(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            token=token,
            api_key=api_key,
        )

        if stock_client is None:
            stock_base = (
                getattr(settings, "STOCK_API_BASE_URL", None)
                or getattr(settings, "STOCK_API_BASE", None)
                or base_por_defecto
            )
            stock_client = StockClient(base_url=stock_base)
        self.stock_client = stock_client

    # ------------------------------------------------------------------
    # Endpoints principales del servicio de carrito
    # ------------------------------------------------------------------
    def obtener_carrito(self, usuario_id: int) -> Dict[str, Any]:
        """Obtiene el carrito activo del usuario indicado."""
        params = {"usuarioId": usuario_id}
        return self.get("/shopcart/", params=params, expected_status=200)

    def obtener_items(self, usuario_id: int) -> List[Dict[str, Any]]:
        """Devuelve únicamente los ítems del carrito para un usuario."""
        carrito = self.obtener_carrito(usuario_id)
        if isinstance(carrito, dict):
            items = carrito.get("items", [])
            return items if isinstance(items, list) else []
        return []

    def agregar_producto(self, usuario_id: int, producto_id: int, cantidad: int = 1) -> Dict[str, Any]:
        """Agrega un producto al carrito del usuario."""
        payload = {"usuarioId": usuario_id, "productId": producto_id, "quantity": int(cantidad)}
        return self.post("/shopcart/", json=payload, expected_status=(200, 201))

    def actualizar_producto(self, usuario_id: int, producto_id: int, cantidad: int) -> Dict[str, Any]:
        """Actualiza la cantidad de un producto específico."""
        payload = {"usuarioId": usuario_id, "quantity": int(cantidad)}
        return self.put(f"/shopcart/{producto_id}/", json=payload, expected_status=(200, 204))

    def eliminar_producto(self, usuario_id: int, producto_id: int) -> Any:
        """Elimina un producto del carrito del usuario."""
        payload = {"usuarioId": usuario_id}
        return self.request("DELETE", f"/shopcart/{producto_id}/", json=payload, expected_status=(200, 204))

    def vaciar_carrito(self, usuario_id: int) -> Any:
        """Elimina todos los productos del carrito del usuario."""
        payload = {"usuarioId": usuario_id}
        return self.request("DELETE", "/shopcart/", json=payload, expected_status=(200, 204))

    def sincronizar_carrito(self, usuario_id: int, items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        """Reemplaza completamente el contenido del carrito del usuario."""
        payload = {"usuarioId": usuario_id, "items": list(items)}
        return self.put("/shopcart/", json=payload, expected_status=(200, 204))



def obtener_cliente_carrito(**kwargs: Any) -> CarritoAPIClient:
    """Helper para instanciar el cliente con la configuración del proyecto."""
    base_por_defecto = getattr(settings, "base_url_api", "http://localhost:8000/api/")
    base_url = getattr(settings, "CARRITO_API_BASE_URL", base_por_defecto) or base_por_defecto
    return CarritoAPIClient(base_url=base_url, **kwargs)
