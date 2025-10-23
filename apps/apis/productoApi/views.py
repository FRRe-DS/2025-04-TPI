from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import  Categoria
from .serializer import CategoriaSerializer
from rest_framework import status
from utils.apiCliente.stock import StockClient
from django.conf import settings


class CategoriaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar categorías
    Proporciona automáticamente: list, create, retrieve, update, destroy
    """
    queryset = Categoria.objects.filter(activo=True)
    serializer_class = CategoriaSerializer
    
    def get_queryset(self):
        """Filtra solo categorías activas"""
        return Categoria.objects.filter(activo=True).order_by('nombre')


class ProductoViewSet(viewsets.ViewSet):
    """
    ViewSet para gestionar productos desde la API externa de Stock
    """
    
    def list(self, request):
        """GET /productos/ - Listar productos"""
        # Modo prueba: devolver listado hardcodeado (no llamar a la API de Stock)
        productos = [
            {
                "id": 1,
                "nombre": "Remera básica",
                "descripcion": "Remera de algodón 100% peinado",
                "precio": 999.99,
                "stock": 50,
                "categoriaId": 1,
                "imagenUrl": "/static/imagenes/ropa_prueba.webp",
            },
            {
                "id": 2,
                "nombre": "Pantalón jean",
                "descripcion": "Jean slim fit azul oscuro",
                "precio": 14999.0,
                "stock": 35,
                "categoriaId": 2,
                "imagenUrl": "/static/imagenes/ropa_prueba_atras.webp",
            },
            {
                "id": 3,
                "nombre": "Zapatillas urbanas",
                "descripcion": "Zapatillas livianas para uso diario",
                "precio": 24999.9,
                "stock": 20,
                "categoriaId": 3,
                "imagenUrl": "/static/imagenes/logo.png",
            },
            {
                "id": 4,
                "nombre": "Campera liviana",
                "descripcion": "Campera rompeviento impermeable",
                "precio": 32999.5,
                "stock": 12,
                "categoriaId": 4,
                "imagenUrl": "/static/imagenes/heroTecno.png",
            },
            {
                "id": 5,
                "nombre": "Buzo canguro",
                "descripcion": "Buzo con capucha, friza liviana",
                "precio": 18999.0,
                "stock": 40,
                "categoriaId": 1,
                "imagenUrl": "/static/imagenes/remera_categoria.jpg",
            },
        ]

        return Response(productos, status=status.HTTP_200_OK)
        stock_client = StockClient(base_url=settings.STOCK_API_BASE_URL)
        try:
            categoria = request.query_params.get('categoria')
            search = request.query_params.get('search')
            page = request.query_params.get('page', 1)
            limit = request.query_params.get('limit', 20)
            
            productos = stock_client.listar_productos(
                page=int(page),
                limit=int(limit),
                q=search,
                categoriaId=int(categoria) if categoria else None
            )
            return Response(productos, status=status.HTTP_200_OK)
        except Exception as e:
            if 'Connection' in str(e):
                return Response({
                    "error": "Servicio Stock no disponible", 
                    "code": "STOCK_SERVICE_UNAVAILABLE"
                }, status=status.HTTP_502_BAD_GATEWAY)
            return Response({
                "error": "Error interno del servidor", 
                "code": "INTERNAL_ERROR"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def retrieve(self, request, pk=None):
        """GET /productos/{id}/ - Detalle de producto"""
        stock_client = StockClient(base_url=settings.STOCK_API_BASE_URL)
        try:
            producto = stock_client.obtener_producto(int(pk))
            if not producto:
                return Response({
                    "error": "Producto no encontrado", 
                    "code": "PRODUCT_NOT_FOUND"
                }, status=status.HTTP_404_NOT_FOUND)
            return Response(producto, status=status.HTTP_200_OK)
        except Exception as e:
            if 'Connection' in str(e):
                return Response({
                    "error": "Servicio Stock no disponible", 
                    "code": "STOCK_SERVICE_UNAVAILABLE"
                }, status=status.HTTP_502_BAD_GATEWAY)
            return Response({
                "error": "Error interno del servidor", 
                "code": "INTERNAL_ERROR"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
