from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Carrito, ItemCarrito
from .serializer import CartSerializer
from .client import obtener_cliente_carrito
from rest_framework.permissions import AllowAny, IsAuthenticated

class CartViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def list(self, request):
        """GET /api/shopcart/ - Ver carrito"""
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        items = carrito.items.all()
        product_ids = [item.producto_id for item in items]
        carrito_client = obtener_cliente_carrito()
        productos = carrito_client.obtener_productos_por_ids(product_ids)
        serializer = CartSerializer(carrito, context={'productos': productos})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        """POST /api/shopcart/ - Agregar al carrito"""
        carrito, _ = Carrito.objects.get_or_create()
        
        print('se creo el carrito sres')

        product_id = request.data.get('productId')
        quantity = request.data.get('quantity', 1)
        if not product_id or int(quantity) < 1:
            return Response({"error": "Datos inválidos", "code": "INVALID_DATA"}, status=status.HTTP_400_BAD_REQUEST)
        carrito_client = obtener_cliente_carrito()
        producto = carrito_client.obtener_productos_por_ids([product_id]).get(product_id)
        if not producto:
            return Response({"error": "Producto no encontrado", "code": "PRODUCT_NOT_FOUND"}, status=status.HTTP_404_NOT_FOUND)
        item, created = ItemCarrito.objects.get_or_create(carrito=carrito, producto_id=product_id)
        item.cantidad += int(quantity)
        item.save()
        return Response({"message": "Producto agregado al carrito"}, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        """PUT /api/shopcart/{productId}/ - Actualizar cantidad"""
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        quantity = request.data.get('quantity')
        if pk is None or quantity is None or int(quantity) < 1:
            return Response({"error": "Cantidad inválida", "code": "INVALID_QUANTITY"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            item = ItemCarrito.objects.get(carrito=carrito, producto_id=pk)
            item.cantidad = int(quantity)
            item.save()
            return Response({"message": "Carrito actualizado"}, status=status.HTTP_200_OK)
        except ItemCarrito.DoesNotExist:
            return Response({"error": "Producto no encontrado en el carrito", "code": "CART_ITEM_NOT_FOUND"}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        """DELETE /api/shopcart/{productId}/ - Remover producto o vaciar carrito"""
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user) #no se necesita pq es autenticacion
        if pk:
            try:
                item = ItemCarrito.objects.get(carrito=carrito, producto_id=pk)
                item.delete()
                return Response({"message": "Producto removido del carrito"}, status=status.HTTP_200_OK)
            except ItemCarrito.DoesNotExist:
                return Response({"error": "Producto no encontrado en el carrito", "code": "CART_ITEM_NOT_FOUND"}, status=status.HTTP_404_NOT_FOUND)
        else:
            carrito.items.all().delete()
            return Response({"message": "Carrito vaciado"}, status=status.HTTP_200_OK)
        
        