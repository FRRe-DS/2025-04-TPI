from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.conf import settings
from .models import Carrito, ItemCarrito
from .serializer import CartSerializer
from .client import obtener_cliente_stock


class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """GET /api/shopcart/ - Ver carrito"""
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        
        # Verificar si usamos APIs externas o modo mock/desarrollo
        use_external_apis = not getattr(settings, 'USE_MOCK_APIS', True)
        productos = []
        
        if use_external_apis:
            # Modo PRODUCCIÓN: Obtener datos reales de la API de Stock
            items = carrito.items.all()
            product_ids = [item.producto_id for item in items]
            stock_client = obtener_cliente_stock()
            
            for id in product_ids:            
                producto = stock_client.obtener_producto(id)
                if not producto:
                    return Response(
                        {"error": "Error al obtener productos del carrito", "code": "PRODUCT_FETCH_ERROR"}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                productos.append(producto)
        else:
            # Modo DESARROLLO/MOCK: No llamar a APIs externas
            # El serializer solo mostrará los IDs de productos y cantidades
            pass
        
        serializer = CartSerializer(carrito, context={'productos': productos})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        """POST /api/shopcart/ - Agregar al carrito"""
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)

        product_id = request.data.get('productId')
        quantity = request.data.get('quantity', 1)
        if not product_id or int(quantity) < 1:
            return Response({"error": "Datos inválidos", "code": "INVALID_DATA"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si usamos APIs externas o modo mock/desarrollo
        use_external_apis = not getattr(settings, 'USE_MOCK_APIS', True)
        
        if use_external_apis:
            # Modo PRODUCCIÓN: Verificar con la API de Stock real
            stock_client = obtener_cliente_stock()
            producto = stock_client.obtener_producto(product_id)
            if not producto:
                return Response(
                    {"error": "Producto no encontrado", "code": "PRODUCT_NOT_FOUND"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Modo DESARROLLO/MOCK: Confiar en que el productId es válido
            # No verificamos con Stock porque es una API externa no disponible
            pass
        
        item, created = ItemCarrito.objects.get_or_create(carrito=carrito, producto_id=product_id)
        if not created:
            item.cantidad += int(quantity)
        else:
            item.cantidad = int(quantity)
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
        """DELETE /api/shopcart/{productId}/ - Remover producto o vaciar carrito""" #a que usuario?? pensalo
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
        
        
