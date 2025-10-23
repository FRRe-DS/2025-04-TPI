"""
Tests automatizados para la API Mock de Stock
Cubre todos los endpoints y casos edge
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.apis.stockApi.models import Producto, Categoria, Reserva, DetalleReserva
from datetime import datetime


class StockAPITestCase(TestCase):
    """Tests para los endpoints de Stock API Mock"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.client = APIClient()
        
        # Crear categorías de prueba
        self.categoria_ropa = Categoria.objects.create(
            nombre="Ropa",
            descripcion="Prendas de vestir"
        )
        self.categoria_tech = Categoria.objects.create(
            nombre="Tecnología",
            descripcion="Dispositivos electrónicos"
        )
        
        # Crear productos de prueba
        self.producto1 = Producto.objects.create(
            nombre="Remera Básica",
            descripcion="Remera de algodón",
            precio=2500.00,
            stock_disponible=50,
            categoria=self.categoria_ropa
        )
        self.producto2 = Producto.objects.create(
            nombre="Jean Slim Fit",
            descripcion="Jean de mezclilla",
            precio=8500.00,
            stock_disponible=30,
            categoria=self.categoria_ropa
        )
        self.producto3 = Producto.objects.create(
            nombre="Auriculares Bluetooth",
            descripcion="Auriculares inalámbricos",
            precio=15000.00,
            stock_disponible=0,  # Sin stock
            categoria=self.categoria_tech
        )
    
    def test_listar_productos_success(self):
        """Test: Listar productos exitosamente"""
        url = '/api/mock/stock/productos/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.json())
        self.assertIn('pagination', response.json())
        self.assertEqual(len(response.json()['data']), 3)
    
    def test_listar_productos_con_paginacion(self):
        """Test: Paginación funciona correctamente"""
        url = '/api/mock/stock/productos/?page=1&limit=2'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data['data']), 2)
        self.assertEqual(data['pagination']['page'], 1)
        self.assertEqual(data['pagination']['total'], 3)
    
    def test_listar_productos_filtrar_por_categoria(self):
        """Test: Filtrar productos por categoría"""
        url = f'/api/mock/stock/productos/?categoria_id={self.categoria_tech.id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['nombre'], "Auriculares Bluetooth")
    
    def test_obtener_producto_por_id_success(self):
        """Test: Obtener producto específico por ID"""
        url = f'/api/mock/stock/productos/{self.producto1.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['id'], self.producto1.id)
        self.assertEqual(data['nombre'], "Remera Básica")
        self.assertEqual(data['stock_disponible'], 50)
    
    def test_obtener_producto_no_existe(self):
        """Test: Error al buscar producto inexistente"""
        url = '/api/mock/stock/productos/999/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_listar_categorias_success(self):
        """Test: Listar todas las categorías"""
        url = '/api/mock/stock/categorias/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data['data']), 2)
    
    def test_reservar_stock_success(self):
        """Test: Reservar stock exitosamente"""
        url = '/api/mock/stock/reservar/'
        payload = {
            "idCompra": "TEST-001",
            "usuarioId": 100,
            "productos": [
                {"idProducto": self.producto1.id, "cantidad": 5},
                {"idProducto": self.producto2.id, "cantidad": 2}
            ]
        }
        response = self.client.post(url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn('idReserva', data)
        self.assertEqual(data['estado'], 'PENDIENTE')
        self.assertEqual(data['idCompra'], "TEST-001")
        
        # Verificar que el stock se redujo
        self.producto1.refresh_from_db()
        self.assertEqual(self.producto1.stock_disponible, 45)  # 50 - 5
    
    def test_reservar_stock_sin_stock_suficiente(self):
        """Test: Error al reservar más stock del disponible"""
        url = '/api/mock/stock/reservar/'
        payload = {
            "idCompra": "TEST-002",
            "usuarioId": 100,
            "productos": [
                {"idProducto": self.producto1.id, "cantidad": 100}  # Más de 50
            ]
        }
        response = self.client.post(url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.json())
    
    def test_reservar_stock_producto_sin_stock(self):
        """Test: Error al reservar producto sin stock"""
        url = '/api/mock/stock/reservar/'
        payload = {
            "idCompra": "TEST-003",
            "usuarioId": 100,
            "productos": [
                {"idProducto": self.producto3.id, "cantidad": 1}  # Stock = 0
            ]
        }
        response = self.client.post(url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_reservar_stock_producto_no_existe(self):
        """Test: Error al reservar producto inexistente"""
        url = '/api/mock/stock/reservar/'
        payload = {
            "idCompra": "TEST-004",
            "usuarioId": 100,
            "productos": [
                {"idProducto": 999, "cantidad": 1}
            ]
        }
        response = self.client.post(url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_reservar_stock_datos_invalidos(self):
        """Test: Validación de datos de entrada"""
        url = '/api/mock/stock/reservar/'
        
        # Sin idCompra
        payload = {
            "usuarioId": 100,
            "productos": [{"idProducto": self.producto1.id, "cantidad": 1}]
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Cantidad negativa
        payload = {
            "idCompra": "TEST-005",
            "usuarioId": 100,
            "productos": [{"idProducto": self.producto1.id, "cantidad": -1}]
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_liberar_stock_success(self):
        """Test: Liberar stock de una reserva"""
        # Primero crear una reserva
        reserva = Reserva.objects.create(
            id_compra="TEST-LIB-001",
            usuario_id=100,
            estado="PENDIENTE"
        )
        DetalleReserva.objects.create(
            reserva=reserva,
            producto=self.producto1,
            cantidad=10
        )
        
        # Reducir stock manualmente
        stock_original = self.producto1.stock_disponible
        self.producto1.stock_disponible -= 10
        self.producto1.save()
        
        # Liberar stock
        url = '/api/mock/stock/liberar/'
        payload = {
            "idReserva": reserva.id,
            "usuarioId": 100
        }
        response = self.client.post(url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['estado'], 'LIBERADO')
        
        # Verificar que el stock se restauró
        self.producto1.refresh_from_db()
        self.assertEqual(self.producto1.stock_disponible, stock_original)
    
    def test_liberar_stock_reserva_no_existe(self):
        """Test: Error al liberar reserva inexistente"""
        url = '/api/mock/stock/liberar/'
        payload = {
            "idReserva": 999,
            "usuarioId": 100
        }
        response = self.client.post(url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_listar_reservas_por_usuario(self):
        """Test: Listar reservas de un usuario específico"""
        # Crear reservas de prueba
        Reserva.objects.create(
            id_compra="TEST-USR-001",
            usuario_id=100,
            estado="PENDIENTE"
        )
        Reserva.objects.create(
            id_compra="TEST-USR-002",
            usuario_id=100,
            estado="CONFIRMADA"
        )
        Reserva.objects.create(
            id_compra="TEST-USR-003",
            usuario_id=200,  # Otro usuario
            estado="PENDIENTE"
        )
        
        url = '/api/mock/stock/reservas/?usuarioId=100'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data['data']), 2)
        self.assertEqual(data['pagination']['total'], 2)
    
    def test_listar_reservas_sin_usuario_id(self):
        """Test: Error al listar reservas sin usuarioId"""
        url = '/api/mock/stock/reservas/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_obtener_detalle_reserva(self):
        """Test: Obtener detalles de una reserva específica"""
        reserva = Reserva.objects.create(
            id_compra="TEST-DET-001",
            usuario_id=100,
            estado="PENDIENTE"
        )
        DetalleReserva.objects.create(
            reserva=reserva,
            producto=self.producto1,
            cantidad=5
        )
        
        url = f'/api/mock/stock/reservas/{reserva.id}/?usuarioId=100'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['idReserva'], reserva.id)
        self.assertEqual(len(data['detalles']), 1)
    
    def test_confirmacion_automatica_reserva_confirmada(self):
        """Test: Una reserva CONFIRMADA no puede ser liberada"""
        reserva = Reserva.objects.create(
            id_compra="TEST-CONF-001",
            usuario_id=100,
            estado="CONFIRMADA"
        )
        
        url = '/api/mock/stock/liberar/'
        payload = {
            "idReserva": reserva.id,
            "usuarioId": 100
        }
        response = self.client.post(url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class StockModelTestCase(TestCase):
    """Tests para los modelos de Stock"""
    
    def setUp(self):
        """Configuración inicial"""
        self.categoria = Categoria.objects.create(
            nombre="Test",
            descripcion="Categoría de prueba"
        )
        self.producto = Producto.objects.create(
            nombre="Producto Test",
            descripcion="Descripción test",
            precio=1000.00,
            stock_disponible=20,
            categoria=self.categoria
        )
    
    def test_producto_tiene_stock(self):
        """Test: Verificar método tiene_stock()"""
        self.assertTrue(self.producto.tiene_stock(5))
        self.assertTrue(self.producto.tiene_stock(20))
        self.assertFalse(self.producto.tiene_stock(21))
    
    def test_producto_reservar_stock(self):
        """Test: Método reservar() reduce el stock"""
        self.producto.reservar(10)
        self.assertEqual(self.producto.stock_disponible, 10)
    
    def test_producto_liberar_stock(self):
        """Test: Método liberar() aumenta el stock"""
        self.producto.reservar(10)  # Stock = 10
        self.producto.liberar(5)    # Stock = 15
        self.assertEqual(self.producto.stock_disponible, 15)
    
    def test_categoria_str(self):
        """Test: Representación string de Categoría"""
        self.assertEqual(str(self.categoria), "Test")
    
    def test_producto_str(self):
        """Test: Representación string de Producto"""
        self.assertEqual(str(self.producto), "Producto Test")
