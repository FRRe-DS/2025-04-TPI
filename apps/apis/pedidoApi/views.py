from __future__ import annotations

from decimal import Decimal
from django.db import transaction
from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from utils.apiCliente import APIError

from apps.apis.carritoApi.models import Carrito


from .client import obtener_cliente_logistica, obtener_cliente_stock
from .models import Pedido, DireccionEnvio, DetallePedido
from .serializer import PedidoSerializer


class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.select_related("direccion_envio", "usuario").prefetch_related("detalles")
    serializer_class = PedidoSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        usuario = self.request.user
        if usuario.is_authenticated and not usuario.is_staff:
            queryset = queryset.filter(usuario=usuario)
        return queryset

    def perform_create(self, serializador):
        serializador.save()

    def destroy(self, request, *args, **kwargs):
        pedido = self.get_object()
        if pedido.estado == Pedido.Estado.CONFIRMADO:
            return Response(
                {"detail": "No se puede eliminar un pedido confirmado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="confirmar")
    def confirmar(self, request, pk=None):
        pedido = self.get_object()

        if pedido.estado == Pedido.Estado.CONFIRMADO:
            return Response(
                {"detail": "El pedido ya se encuentra confirmado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if pedido.estado == Pedido.Estado.CANCELADO:
            return Response(
                {"detail": "No es posible confirmar un pedido cancelado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if pedido.detalles.count() == 0:
            return Response(
                {"detail": "El pedido no tiene productos asociados."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tipo_transporte = request.data.get("tipo_transporte") or pedido.tipo_transporte
        if not tipo_transporte:
            return Response(
                {"detail": "Debe especificarse un tipo de transporte para confirmar el pedido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pedido.tipo_transporte = tipo_transporte
        pedido.save(update_fields=["tipo_transporte", "actualizado_en"])

        cliente_logistica = obtener_cliente_logistica()
        cliente_stock = obtener_cliente_stock()

        detalles_pedido = list(pedido.detalles.all())
        productos_logistica = [
            {"id": detalle.producto_id, "quantity": detalle.cantidad}
            for detalle in detalles_pedido
        ]
        productos_stock = [
            {"idProducto": detalle.producto_id, "cantidad": detalle.cantidad}
            for detalle in detalles_pedido
        ]

        if pedido.total == Decimal("0.00"):
            pedido.recalcular_total(guardar=True)

        try:
            respuesta_envio = cliente_logistica.create_shipment(
                order_id=pedido.id,
                user_id=pedido.usuario_id or (request.user.id if request.user.is_authenticated else 0),
                delivery_address=pedido.direccion_envio.generar_datos_logistica(),
                transport_type=tipo_transporte,
                products=productos_logistica,
            )
        except APIError as exc:
            return Response(
                {
                    "detail": "Error al crear el envío.",
                    "error": str(exc),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        referencia_envio = (
            respuesta_envio.get("id")
            or respuesta_envio.get("shipping_id")
            or respuesta_envio.get("reference")
        )

        if not referencia_envio:
            return Response(
                {
                    "detail": "La API de envíos no devolvió un identificador válido.",
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        try:
            respuesta_stock = cliente_stock.reservar_stock(
                idCompra=str(pedido.id),
                usuarioId=pedido.usuario_id or (request.user.id if request.user.is_authenticated else 0),
                productos=productos_stock,
            )
        except APIError as exc:
            return Response(
                {
                    "detail": "Error al reservar el stock.",
                    "error": str(exc),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        referencia_stock = (
            respuesta_stock.get("idReserva")
            or respuesta_stock.get("reserva_id")
            or respuesta_stock.get("id")
        )

        if not referencia_stock:
            return Response(
                {
                    "detail": "La API de stock no devolvió un identificador de reserva.",
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        pedido.marcar_confirmado(
            referencia_envio=referencia_envio,
            referencia_reserva_stock=referencia_stock,
        )

        serializador = self.get_serializer(pedido)
        return Response(serializador.data)

    @action(detail=True, methods=["delete"], url_path="cancelar")
    def cancelar(self, request, pk=None):
        """Cancelar un pedido que aún no ha sido confirmado."""
        pedido = self.get_object()

        if pedido.estado == Pedido.Estado.CANCELADO:
            return Response(
                {
                    "error": "El pedido ya se encuentra cancelado",
                    "code": "ORDER_ALREADY_CANCELLED"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if pedido.estado == Pedido.Estado.CONFIRMADO:
            return Response(
                {
                    "error": "No se puede cancelar un pedido ya confirmado",
                    "code": "CANNOT_CANCEL_SHIPPED_ORDER"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Si el pedido tiene referencias de stock o envío, intentamos cancelarlas
        if pedido.referencia_reserva_stock or pedido.referencia_envio:
            cliente_stock = obtener_cliente_stock()
            cliente_logistica = obtener_cliente_logistica()

            errores_cancelacion = []

            # Cancelar reserva de stock si existe
            if pedido.referencia_reserva_stock:
                try:
                    cliente_stock.cancelar_reserva(
                        idReserva=pedido.referencia_reserva_stock,
                        idCompra=str(pedido.id)
                    )
                except APIError as exc:
                    errores_cancelacion.append(f"Stock: {str(exc)}")

            # Cancelar envío si existe
            if pedido.referencia_envio:
                try:
                    cliente_logistica.cancel_shipment(
                        shipping_id=pedido.referencia_envio,
                        order_id=pedido.id
                    )
                except APIError as exc:
                    errores_cancelacion.append(f"Envío: {str(exc)}")

            # Si hubo errores en la cancelación de servicios externos, devolver error
            if errores_cancelacion:
                return Response(
                    {
                        "error": "Error al cancelar servicios externos",
                        "code": "EXTERNAL_SERVICE_ERROR",
                        "detail": ", ".join(errores_cancelacion)
                    },
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        # Marcar el pedido como cancelado usando una transacción
        with transaction.atomic():
            pedido.estado = Pedido.Estado.CANCELADO
            pedido.save(update_fields=["estado", "actualizado_en"])

        return Response(
            {
                "message": "Pedido cancelado exitosamente"
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["get"], url_path="history")
    def history(self, request):
        """GET /api/shopcart/history - Ver historial de pedidos del usuario autenticado"""
        queryset = self.get_queryset()  # Ya está filtrado por usuario en get_queryset
        serializer = self.get_serializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="history-detail")
    def history_detail(self, request, pk=None):
        """GET /api/shopcart/history/{id} - Ver un pedido específico"""
        try:
            pedido = self.get_object()  # Más simple: usa get_object() que ya maneja pk
            serializer = self.get_serializer(pedido, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Pedido.DoesNotExist:
            return Response(
                {
                    "error": "Pedido no encontrado",
                    "code": "ORDER_NOT_FOUND"
                },
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["post"], url_path="checkout")
    def crear_desde_carrito(self, request):
        """POST /api/shopcart/checkout - Crear pedido desde carrito del usuario autenticado"""
        
        # Verificar autenticación
        if not request.user.is_authenticated:
            return Response(
                {"error": "Autenticación requerida", "code": "AUTHENTICATION_REQUIRED"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        
        # Obtener carrito del usuario
        try:
            carrito = Carrito.objects.get(usuario=request.user)
        except Carrito.DoesNotExist:
            return Response(
                {"error": "No tienes un carrito activo", "code": "CART_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Verificar que el carrito tenga items
        items_carrito = carrito.items.all()
        if not items_carrito.exists():
            return Response(
                {"error": "El carrito está vacío", "code": "EMPTY_CART"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Extraer datos de dirección del payload
        direccion_envio = request.data.get("direccion_envio")
        metodo_pago = request.data.get("metodo_pago", "tarjeta")
        
        # Validar que se haya enviado la dirección
        if not direccion_envio:
            return Response(
                {"error": "Falta dirección de envío", "code": "MISSING_ADDRESS"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Extraer campos de la dirección (formato del script: string simple)
        # Si direccion_envio es un string, parsearlo; si es dict, usarlo directamente
        if isinstance(direccion_envio, str):
            # Formato simple: "Calle Falsa 123, Resistencia, Chaco, Argentina"
            calle = direccion_envio
            ciudad = "Ciudad por defecto"
            cp = "0000"
            nombre_receptor = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
        else:
            # Formato estructurado (dict)
            calle = direccion_envio.get("calle", "")
            ciudad = direccion_envio.get("ciudad", "")
            cp = direccion_envio.get("codigo_postal", "")
            nombre_receptor = direccion_envio.get("nombre_receptor") or f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username

        # Crear dirección de envío
        with transaction.atomic():
            direccion = DireccionEnvio.objects.create(
                calle=calle,
                ciudad=ciudad,
                codigo_postal=cp,
                nombre_receptor=nombre_receptor,
                provincia=direccion_envio.get("provincia", "") if isinstance(direccion_envio, dict) else "",
                telefono=direccion_envio.get("telefono", "") if isinstance(direccion_envio, dict) else "",
                pais="Argentina",
            )

            # Crear pedido
            pedido = Pedido.objects.create(
                usuario=request.user,
                direccion_envio=direccion,
                estado=Pedido.Estado.PENDIENTE,
                tipo_transporte=request.data.get("tipo_transporte", "domicilio"),
                total=Decimal("0.00")
            )

            # Obtener precios de productos desde la API de Stock (si USE_MOCK_APIS=False)
            # o usar precios por defecto (si USE_MOCK_APIS=True)
            use_external_apis = not getattr(settings, 'USE_MOCK_APIS', True)
            total = Decimal("0.00")
            
            if use_external_apis:
                # Modo PRODUCCIÓN: Obtener precios reales de Stock API
                stock_client = obtener_cliente_stock()
                
                for item in items_carrito:
                    try:
                        producto = stock_client.obtener_producto(item.producto_id)
                        precio_unitario = Decimal(str(producto.get("price", 0)))
                        nombre_producto = producto.get("name", f"Producto {item.producto_id}")
                    except Exception:
                        # Si falla la API, usar valores por defecto
                        precio_unitario = Decimal("0.00")
                        nombre_producto = f"Producto {item.producto_id}"
                    
                    subtotal = precio_unitario * item.cantidad
                    total += subtotal

                    DetallePedido.objects.create(
                        pedido=pedido,
                        producto_id=item.producto_id,
                        nombre_producto=nombre_producto,
                        cantidad=item.cantidad,
                        precio_unitario=precio_unitario,
                    )
            else:
                # Modo DESARROLLO/MOCK: Usar precios ficticios
                precios_mock = {
                    1: Decimal("1299.99"),
                    2: Decimal("999.00"),
                    3: Decimal("849.00"),
                    4: Decimal("249.00"),
                    5: Decimal("89.99"),
                }
                
                for item in items_carrito:
                    precio_unitario = precios_mock.get(item.producto_id, Decimal("99.99"))
                    subtotal = precio_unitario * item.cantidad
                    total += subtotal

                    DetallePedido.objects.create(
                        pedido=pedido,
                        producto_id=item.producto_id,
                        nombre_producto=f"Producto {item.producto_id}",
                        cantidad=item.cantidad,
                        precio_unitario=precio_unitario,
                    )

            # Actualizar total del pedido
            pedido.total = total
            pedido.save(update_fields=["total"])
            
            # Vaciar el carrito después de crear el pedido
            items_carrito.delete()

            serializer = self.get_serializer(pedido)
            return Response({
                "message": "Pedido creado exitosamente",
                "pedido_id": pedido.id,
                "pedido": serializer.data
            }, status=status.HTTP_201_CREATED)

    # --------------------------------------------------------------
    # Tracking de envíos (integración Compras ↔ Logística)
    # --------------------------------------------------------------
    @action(detail=True, methods=["post"], url_path="tracking")
    def crear_tracking(self, request, pk=None):
        """Vincula un pedido con un envío en Logística creando un tracking.

        Crea el tracking en el servicio de Logística y guarda la referencia
        en el pedido (campo referencia_envio).
        """
        pedido = self.get_object()

        if pedido.referencia_envio:
            return Response(
                {"error": "El pedido ya tiene un tracking asociado", "code": "ALREADY_LINKED"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if pedido.detalles.count() == 0:
            return Response(
                {"error": "El pedido no tiene productos asociados", "code": "NO_PRODUCTS"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tipo_transporte = request.data.get("tipo_transporte") or pedido.tipo_transporte
        if not tipo_transporte:
            return Response(
                {"error": "Debe especificarse un tipo de transporte", "code": "MISSING_TRANSPORT_TYPE"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cliente_logistica = obtener_cliente_logistica()

        productos_logistica = [
            {"id": d.producto_id, "quantity": d.cantidad}
            for d in pedido.detalles.all()
        ]

        try:
            resp = cliente_logistica.create_tracking(
                order_id=pedido.id,
                user_id=pedido.usuario_id or (request.user.id if request.user.is_authenticated else 0),
                delivery_address=pedido.direccion_envio.generar_datos_logistica(),
                transport_type=tipo_transporte,
                products=productos_logistica,
            )
        except APIError as exc:
            return Response(
                {"error": "Error al crear el tracking", "code": "EXTERNAL_SERVICE_ERROR", "detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        tracking_id = (
            resp.get("id")
            or resp.get("tracking_id")
            or resp.get("shipping_id")
            or resp.get("reference")
        )

        if not tracking_id:
            return Response(
                {"error": "La API de logística no devolvió un identificador de tracking", "code": "EXTERNAL_SERVICE_ERROR"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Guardar referencia del tracking en el pedido
        pedido.referencia_envio = str(tracking_id)
        pedido.save(update_fields=["referencia_envio", "actualizado_en"])

        return Response({"tracking": resp, "pedido_id": pedido.id}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="tracking")
    def obtener_tracking(self, request, pk=None):
        """Obtiene el estado del envío/tracking asociado al pedido."""
        pedido = self.get_object()
        if not pedido.referencia_envio:
            return Response(
                {"error": "El pedido no tiene tracking asociado", "code": "NO_TRACKING"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cliente_logistica = obtener_cliente_logistica()
        tracking_id = pedido.referencia_envio

        try:
            data = cliente_logistica.get_tracking(int(tracking_id))
        except APIError:
            # Fallback: algunos servicios exponen shipping como detalle
            try:
                data = cliente_logistica.get_shipment(int(tracking_id))
            except APIError as exc2:
                return Response(
                    {"error": "Error al obtener el tracking", "code": "EXTERNAL_SERVICE_ERROR", "detail": str(exc2)},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        return Response({"tracking": data, "pedido_id": pedido.id}, status=status.HTTP_200_OK)
