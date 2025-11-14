from __future__ import annotations

from decimal import Decimal
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from utils.apiCliente import APIError

from apps.apis.carritoApi.models import Carrito
from apps.apis.carritoApi.client import obtener_cliente_carrito

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
        """POST /api/shopcart/checkout - Crear pedido desde carrito mock (sin autenticación)"""
        
        # Obtener items mock del payload
        items = request.data.get("items", [])

        if not items:
            return Response(
                {"error": "El carrito mock está vacío", "code": "EMPTY_CART"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Extraer datos de dirección del payload
        nombre_receptor = request.data.get("nombre_receptor")
        tipo_transporte = request.data.get("tipo_transporte", "domicilio")
        
        # Validar datos mínimos comunes
        if not nombre_receptor:
            return Response(
                {"error": "Falta nombre del receptor", "code": "MISSING_DATA"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Validar dirección solo si NO es retiro en sucursal
        if tipo_transporte not in ['retiro_sucursal', 'demo_tracking']:
            calle = request.data.get("calle")
            ciudad = request.data.get("ciudad")
            cp = request.data.get("cp")
            if not all([calle, ciudad, cp]):
                return Response(
                    {"error": "Faltan datos de dirección", "code": "MISSING_DATA"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            # Para retiro en sucursal, dirección es opcional
            calle = request.data.get("calle", "")
            ciudad = request.data.get("ciudad", "")
            cp = request.data.get("cp", "")

        departamento = request.data.get("departamento", "")
        telefono = request.data.get("telefono", "")
        costo_envio = Decimal(str(request.data.get("costo_envio", 0)))

        # Crear dirección de envío
        with transaction.atomic():
            direccion = DireccionEnvio.objects.create(
                calle=calle,
                ciudad=ciudad,
                codigo_postal=cp,
                nombre_receptor=nombre_receptor,
                provincia=departamento,
                telefono=telefono,
                pais="Argentina",
            )

            # Crear pedido
            pedido = Pedido.objects.create(
                usuario=None,   # Modo mock, sin autenticación
                direccion_envio=direccion,
                estado=Pedido.Estado.PENDIENTE,
                tipo_transporte=tipo_transporte,
                total=Decimal("0.00")
            )

            # Procesar items mock y crear detalles de pedido
            total = Decimal("0.00")
            for item in items:
                nombre = item.get("nombre", "Producto sin nombre")
                cantidad = int(item.get("cantidad", 1))
                precio = Decimal(str(item.get("precio", 0)))
                subtotal = cantidad * precio
                total += subtotal

                DetallePedido.objects.create(
                    pedido=pedido,
                    producto_id=item.get("id", 0),
                    nombre_producto=nombre,
                    cantidad=cantidad,
                    precio_unitario=precio,
                )

            # 🔥 Agregar costo de envío al total
            total += costo_envio

            # Actualizar total del pedido
            pedido.total = total
            pedido.save(update_fields=["total"])

            serializer = self.get_serializer(pedido)
            return Response({
                "message": "ok",
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
