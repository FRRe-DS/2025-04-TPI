from rest_framework import serializers
from .models import Carrito, ItemCarrito


from utils.apiCliente.stock import StockClient
from django.conf import settings

class CartItemSerializer(serializers.ModelSerializer):
	productId = serializers.IntegerField(source='producto_id')
	quantity = serializers.IntegerField(source='cantidad')
	product = serializers.SerializerMethodField()

	class Meta:
		model = ItemCarrito
		fields = ['productId', 'quantity', 'product']

	def get_product(self, obj):
		# Primero intenta obtener el producto del contexto (batch)
		productos = self.context.get('productos')
		if productos and obj.producto_id in productos:
			return productos[obj.producto_id]
		# Si no hay productos en contexto, hace la petición individual
		try:
			stock_client = StockClient(base_url=settings.STOCK_API_BASE)
			producto = stock_client.obtener_producto(obj.producto_id)
			return producto
		except Exception:
			return None


class CartSerializer(serializers.ModelSerializer):
	items = CartItemSerializer(many=True, read_only=True)
	total = serializers.SerializerMethodField()

	class Meta:
		model = Carrito
		fields = ['items', 'total']

	def get_total(self, obj):
		# Suma de cantidades, puedes ajustar para sumar precios si tienes acceso a los productos
		return sum(item.cantidad for item in obj.items.all())

