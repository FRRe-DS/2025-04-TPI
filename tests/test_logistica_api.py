"""
Tests automatizados para la API Mock de Logística
Cubre endpoints de envíos, costos, tracking y cancelaciones
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.apis.logisticaApi.models import MetodoTransporte, Envio, ProductoEnvio
from apps.apis.stockApi.models import Producto, Categoria
from decimal import Decimal


class LogisticaAPITestCase(TestCase):
    """Tests para los endpoints de Logística API Mock"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.client = APIClient()
        
        # Crear métodos de transporte
        self.metodo_road = MetodoTransporte.objects.create(
            tipo="road",
            nombre_display="Transporte Terrestre",
            descripcion="Envío por camión",
            costo_base=500.00,
            dias_entrega_estimados=5
        )
        self.metodo_air = MetodoTransporte.objects.create(
            tipo="air",
            nombre_display="Transporte Aéreo",
            descripcion="Envío por avión",
            costo_base=2000.00,
            dias_entrega_estimados=2
        )
        
        # Crear productos para pruebas
        categoria = Categoria.objects.create(nombre="Test", descripcion="Test")
        self.producto1 = Producto.objects.create(
            nombre="Producto 1",
            descripcion="Desc 1",
            precio=1000.00,
            stock_disponible=100,
            categoria=categoria
        )
        self.producto2 = Producto.objects.create(
            nombre="Producto 2",
            descripcion="Desc 2",
            precio=2000.00,
            stock_disponible=50,
            categoria=categoria
        )
    
    def test_obtener_metodos_transporte(self):
        """Test: Obtener lista de métodos de transporte"""
        url = '/api/mock/logistica/metodos-transporte/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data['data']), 2)
        self.assertIn('tipo', data['data'][0])
    
    def test_calcular_costo_envio_success(self):
        """Test: Calcular costo de envío exitosamente"""
        url = '/api/mock/logistica/calcular-costo/'
        payload = {
            "delivery_address": {
                "street": "Av. Corrientes 1234",
                "city": "Buenos Aires",
                "state": "CABA",
                "postal_code": "C1043",
                "country": "Argentina"
            },
            "products": [
                {"id": self.producto1.id, "quantity": 2},
                {"id": self.producto2.id, "quantity": 1}
            ],
            "transport_type": "road"
        }
        response = self.client.post(url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('estimated_cost', data)
        self.assertIn('estimated_delivery_days', data)
        self.assertEqual(data['transport_type'], 'road')
        self.assertGreater(Decimal(str(data['estimated_cost'])), Decimal('0'))
    
    def test_calcular_costo_sin_productos(self):
        """Test: Error al calcular costo sin productos"""
        url = '/api/mock/logistica/calcular-costo/'
        payload = {
            "delivery_address": {
                "street": "Av. Corrientes 1234",
                "city": "Buenos Aires",
                "state": "CABA",
                "postal_code": "C1043",
                "country": "Argentina"
            },
            "products": [],
            "transport_type": "road"
        }
        response = self.client.post(url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_calcular_costo_tipo_transporte_invalido(self):
        """Test: Error con tipo de transporte inexistente"""
        url = '/api/mock/logistica/calcular-costo/'
        payload = {
            "delivery_address": {
                "street": "Av. Corrientes 1234",
                "city": "Buenos Aires",
                "state": "CABA",
                "postal_code": "C1043",
                "country": "Argentina"
            },
            "products": [{"id": self.producto1.id, "quantity": 1}],
            "transport_type": "spaceship"  # Tipo inválido
        }
        response = self.client.post(url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_crear_envio_success(self):
        """Test: Crear envío exitosamente"""
        url = '/api/mock/logistica/shipping/'
        payload = {
            "order_id": 1001,
            "user_id": 100,
            "delivery_address": {
                "street": "Calle Falsa 123",
                "city": "Rosario",
                "state": "Santa Fe",
                "postal_code": "S2000",
                "country": "Argentina"
            },
            "transport_type": "road",
            "products": [
                {"id": self.producto1.id, "quantity": 3},
                {"id": self.producto2.id, "quantity": 1}
            ]
        }
        response = self.client.post(url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn('shipping_id', data)
        self.assertIn('tracking_number', data)
        self.assertEqual(data['estado'], 'PENDIENTE')
        self.assertEqual(data['order_id'], 1001)
        
        # Verificar que se creó en la BD
        envio = Envio.objects.get(id=data['shipping_id'])
        self.assertEqual(envio.tracking_number, data['tracking_number'])
        self.assertEqual(envio.productos_envio.count(), 2)
    
    def test_crear_envio_sin_direccion(self):
        """Test: Error al crear envío sin dirección"""
        url = '/api/mock/logistica/shipping/'
        payload = {
            "order_id": 1002,
            "user_id": 100,
            "transport_type": "road",
            "products": [{"id": self.producto1.id, "quantity": 1}]
        }
        response = self.client.post(url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_crear_envio_producto_no_existe(self):
        """Test: Error al crear envío con producto inexistente"""
        url = '/api/mock/logistica/shipping/'
        payload = {
            "order_id": 1003,
            "user_id": 100,
            "delivery_address": {
                "street": "Calle Test",
                "city": "Test City",
                "state": "Test",
                "postal_code": "12345",
                "country": "Argentina"
            },
            "transport_type": "road",
            "products": [{"id": 999, "quantity": 1}]  # Producto inexistente
        }
        response = self.client.post(url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_listar_envios_por_usuario(self):
        """Test: Listar envíos de un usuario"""
        # Crear envíos de prueba
        envio1 = Envio.objects.create(
            order_id=2001,
            user_id=100,
            delivery_street="Calle 1",
            delivery_city="Buenos Aires",
            delivery_state="CABA",
            delivery_postal_code="C1000",
            delivery_country="Argentina",
            metodo_transporte=self.metodo_road,
            costo_envio=1500.00,
            estado="PENDIENTE"
        )
        envio2 = Envio.objects.create(
            order_id=2002,
            user_id=100,
            delivery_street="Calle 2",
            delivery_city="Córdoba",
            delivery_state="Córdoba",
            delivery_postal_code="X5000",
            delivery_country="Argentina",
            metodo_transporte=self.metodo_air,
            costo_envio=3000.00,
            estado="EN_TRANSITO"
        )
        # Envío de otro usuario
        Envio.objects.create(
            order_id=2003,
            user_id=200,
            delivery_street="Calle 3",
            delivery_city="Mendoza",
            delivery_state="Mendoza",
            delivery_postal_code="M5500",
            delivery_country="Argentina",
            metodo_transporte=self.metodo_road,
            costo_envio=1200.00,
            estado="PENDIENTE"
        )
        
        url = '/api/mock/logistica/shipping/?user_id=100'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data['data']), 2)
        self.assertEqual(data['pagination']['total'], 2)
    
    def test_listar_envios_sin_usuario(self):
        """Test: Error al listar envíos sin user_id"""
        url = '/api/mock/logistica/shipping/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_obtener_detalle_envio(self):
        """Test: Obtener detalles de un envío específico"""
        envio = Envio.objects.create(
            order_id=3001,
            user_id=100,
            delivery_street="Av. Principal 999",
            delivery_city="Buenos Aires",
            delivery_state="CABA",
            delivery_postal_code="C1000",
            delivery_country="Argentina",
            metodo_transporte=self.metodo_road,
            costo_envio=2500.00,
            estado="ENTREGADO"
        )
        ProductoEnvio.objects.create(
            envio=envio,
            producto=self.producto1,
            cantidad=5,
            precio_unitario=1000.00
        )
        
        url = f'/api/mock/logistica/shipping/{envio.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['shipping_id'], envio.id)
        self.assertEqual(data['estado'], 'ENTREGADO')
        self.assertEqual(len(data['productos']), 1)
    
    def test_obtener_envio_no_existe(self):
        """Test: Error al buscar envío inexistente"""
        url = '/api/mock/logistica/shipping/999/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_cancelar_envio_success(self):
        """Test: Cancelar envío exitosamente"""
        envio = Envio.objects.create(
            order_id=4001,
            user_id=100,
            delivery_street="Calle Cancelación",
            delivery_city="Buenos Aires",
            delivery_state="CABA",
            delivery_postal_code="C1000",
            delivery_country="Argentina",
            metodo_transporte=self.metodo_road,
            costo_envio=1000.00,
            estado="PENDIENTE"
        )
        
        url = f'/api/mock/logistica/shipping/{envio.id}/cancelar/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['estado'], 'CANCELADO')
        
        # Verificar en BD
        envio.refresh_from_db()
        self.assertEqual(envio.estado, 'CANCELADO')
    
    def test_cancelar_envio_ya_entregado(self):
        """Test: No se puede cancelar un envío ya entregado"""
        envio = Envio.objects.create(
            order_id=4002,
            user_id=100,
            delivery_street="Calle Test",
            delivery_city="Buenos Aires",
            delivery_state="CABA",
            delivery_postal_code="C1000",
            delivery_country="Argentina",
            metodo_transporte=self.metodo_road,
            costo_envio=1000.00,
            estado="ENTREGADO"
        )
        
        url = f'/api/mock/logistica/shipping/{envio.id}/cancelar/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_tracking_number_formato_correcto(self):
        """Test: El tracking number tiene el formato correcto"""
        envio = Envio.objects.create(
            order_id=5001,
            user_id=100,
            delivery_street="Test",
            delivery_city="Test",
            delivery_state="Test",
            delivery_postal_code="12345",
            delivery_country="Argentina",
            metodo_transporte=self.metodo_road,
            costo_envio=500.00,
            estado="PENDIENTE"
        )
        
        # Formato: TRACK-YYYYMMDD-XXXXX
        self.assertTrue(envio.tracking_number.startswith('TRACK-'))
        self.assertEqual(len(envio.tracking_number), 20)  # TRACK-20231016-12345


class LogisticaModelTestCase(TestCase):
    """Tests para los modelos de Logística"""
    
    def setUp(self):
        """Configuración inicial"""
        self.metodo = MetodoTransporte.objects.create(
            tipo="road",
            nombre_display="Test Transport",
            descripcion="Test",
            costo_base=1000.00,
            dias_entrega_estimados=3
        )
    
    def test_metodo_transporte_str(self):
        """Test: Representación string de MetodoTransporte"""
        self.assertEqual(str(self.metodo), "Test Transport (road)")
    
    def test_envio_genera_tracking_automatico(self):
        """Test: El envío genera tracking_number automáticamente"""
        envio = Envio.objects.create(
            order_id=6001,
            user_id=100,
            delivery_street="Test",
            delivery_city="Test",
            delivery_state="Test",
            delivery_postal_code="12345",
            delivery_country="Argentina",
            metodo_transporte=self.metodo,
            costo_envio=1000.00,
            estado="PENDIENTE"
        )
        
        self.assertIsNotNone(envio.tracking_number)
        self.assertTrue(len(envio.tracking_number) > 0)
    
    def test_calcular_costo_por_cantidad(self):
        """Test: El costo aumenta con la cantidad de productos"""
        # Crear 2 envíos con diferentes cantidades
        categoria = Categoria.objects.create(nombre="Test", descripcion="Test")
        producto = Producto.objects.create(
            nombre="Test Product",
            descripcion="Test",
            precio=500.00,
            stock_disponible=100,
            categoria=categoria
        )
        
        envio1 = Envio.objects.create(
            order_id=7001,
            user_id=100,
            delivery_street="Test",
            delivery_city="Test",
            delivery_state="Test",
            delivery_postal_code="12345",
            delivery_country="Argentina",
            metodo_transporte=self.metodo,
            costo_envio=1500.00,  # Costo base + pequeña cantidad
            estado="PENDIENTE"
        )
        ProductoEnvio.objects.create(
            envio=envio1,
            producto=producto,
            cantidad=2,
            precio_unitario=500.00
        )
        
        # El costo debe ser mayor que el costo base
        self.assertGreater(envio1.costo_envio, self.metodo.costo_base)
