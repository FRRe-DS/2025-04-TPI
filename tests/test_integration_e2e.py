"""
Tests de Integración E2E (End-to-End)
Prueba flujos completos que involucran múltiples APIs
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.apis.stockApi.models import Producto, Categoria, Reserva
from apps.apis.logisticaApi.models import MetodoTransporte, Envio
from decimal import Decimal


class IntegracionE2ETestCase(TestCase):
    """Tests de integración que prueban flujos completos"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = APIClient()
        
        # Crear categorías y productos
        self.categoria = Categoria.objects.create(
            nombre="Ropa",
            descripcion="Prendas de vestir"
        )
        self.producto1 = Producto.objects.create(
            nombre="Remera Premium",
            descripcion="Remera de alta calidad",
            precio=3500.00,
            stock_disponible=100,
            categoria=self.categoria
        )
        self.producto2 = Producto.objects.create(
            nombre="Pantalón Cargo",
            descripcion="Pantalón estilo cargo",
            precio=7200.00,
            stock_disponible=50,
            categoria=self.categoria
        )
        
        # Crear métodos de transporte
        self.metodo_road = MetodoTransporte.objects.create(
            tipo="road",
            nombre_display="Transporte Terrestre",
            descripcion="Envío por camión",
            costo_base=500.00,
            dias_entrega_estimados=5
        )
        self.metodo_express = MetodoTransporte.objects.create(
            tipo="express",
            nombre_display="Express",
            descripcion="Envío express 24hs",
            costo_base=1500.00,
            dias_entrega_estimados=1
        )
    
    def test_flujo_compra_completo_exitoso(self):
        """
        Test E2E: Flujo completo de compra
        1. Usuario busca productos
        2. Reserva stock
        3. Calcula costo de envío
        4. Crea envío
        5. Verifica todo el proceso
        """
        # Paso 1: Buscar productos disponibles
        response = self.client.get('/api/mock/stock/productos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        productos = response.json()['data']
        self.assertGreater(len(productos), 0)
        
        # Paso 2: Reservar stock de productos seleccionados
        reserva_payload = {
            "idCompra": "E2E-TEST-001",
            "usuarioId": 888,
            "productos": [
                {"idProducto": self.producto1.id, "cantidad": 3},
                {"idProducto": self.producto2.id, "cantidad": 2}
            ]
        }
        response = self.client.post('/api/mock/stock/reservar/', reserva_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        reserva_data = response.json()
        id_reserva = reserva_data['idReserva']
        
        # Verificar que el stock se redujo
        self.producto1.refresh_from_db()
        self.assertEqual(self.producto1.stock_disponible, 97)  # 100 - 3
        
        # Paso 3: Calcular costo de envío
        costo_payload = {
            "delivery_address": {
                "street": "Av. Corrientes 5000",
                "city": "Buenos Aires",
                "state": "CABA",
                "postal_code": "C1414",
                "country": "Argentina"
            },
            "products": [
                {"id": self.producto1.id, "quantity": 3},
                {"id": self.producto2.id, "quantity": 2}
            ],
            "transport_type": "road"
        }
        response = self.client.post('/api/mock/logistica/calcular-costo/', costo_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        costo_data = response.json()
        costo_estimado = Decimal(str(costo_data['estimated_cost']))
        
        # Paso 4: Crear envío
        envio_payload = {
            "order_id": id_reserva,
            "user_id": 888,
            "delivery_address": {
                "street": "Av. Corrientes 5000",
                "city": "Buenos Aires",
                "state": "CABA",
                "postal_code": "C1414",
                "country": "Argentina"
            },
            "transport_type": "road",
            "products": [
                {"id": self.producto1.id, "quantity": 3},
                {"id": self.producto2.id, "quantity": 2}
            ]
        }
        response = self.client.post('/api/mock/logistica/shipping/', envio_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        envio_data = response.json()
        id_envio = envio_data['shipping_id']
        tracking = envio_data['tracking_number']
        
        # Paso 5: Verificar toda la operación
        # 5.1: Verificar reserva
        response = self.client.get(f'/api/mock/stock/reservas/{id_reserva}/?usuarioId=888')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reserva_verificada = response.json()
        self.assertEqual(reserva_verificada['estado'], 'PENDIENTE')
        
        # 5.2: Verificar envío
        response = self.client.get(f'/api/mock/logistica/shipping/{id_envio}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        envio_verificado = response.json()
        self.assertEqual(envio_verificado['tracking_number'], tracking)
        self.assertEqual(envio_verificado['order_id'], id_reserva)
        
        # 5.3: Verificar stock actualizado
        response = self.client.get(f'/api/mock/stock/productos/{self.producto1.id}/')
        producto_actualizado = response.json()
        self.assertEqual(producto_actualizado['stock_disponible'], 97)
        
        print(f"\n✅ Flujo E2E completado exitosamente:")
        print(f"   - ID Reserva: {id_reserva}")
        print(f"   - ID Envío: {id_envio}")
        print(f"   - Tracking: {tracking}")
        print(f"   - Costo: ${costo_estimado}")
    
    def test_flujo_cancelacion_completo(self):
        """
        Test E2E: Flujo de cancelación
        1. Crear reserva
        2. Crear envío
        3. Cancelar envío
        4. Liberar stock
        """
        # Paso 1: Crear reserva
        reserva_payload = {
            "idCompra": "E2E-CANCEL-001",
            "usuarioId": 777,
            "productos": [
                {"idProducto": self.producto1.id, "cantidad": 5}
            ]
        }
        response = self.client.post('/api/mock/stock/reservar/', reserva_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        id_reserva = response.json()['idReserva']
        
        stock_antes = self.producto1.stock_disponible
        
        # Paso 2: Crear envío
        envio_payload = {
            "order_id": id_reserva,
            "user_id": 777,
            "delivery_address": {
                "street": "Calle Test 123",
                "city": "Rosario",
                "state": "Santa Fe",
                "postal_code": "S2000",
                "country": "Argentina"
            },
            "transport_type": "road",
            "products": [{"id": self.producto1.id, "quantity": 5}]
        }
        response = self.client.post('/api/mock/logistica/shipping/', envio_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        id_envio = response.json()['shipping_id']
        
        # Paso 3: Cancelar envío
        response = self.client.post(f'/api/mock/logistica/shipping/{id_envio}/cancelar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Paso 4: Liberar stock
        liberar_payload = {
            "idReserva": id_reserva,
            "usuarioId": 777
        }
        response = self.client.post('/api/mock/stock/liberar/', liberar_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que el stock se restauró
        self.producto1.refresh_from_db()
        stock_despues = self.producto1.stock_disponible
        self.assertEqual(stock_antes, stock_despues)
        
        print(f"\n✅ Flujo de cancelación completado:")
        print(f"   - Stock restaurado: {stock_despues}")
    
    def test_flujo_multiples_usuarios_concurrentes(self):
        """
        Test E2E: Simular múltiples usuarios comprando simultáneamente
        """
        usuario1_id = 100
        usuario2_id = 200
        usuario3_id = 300
        
        # Usuario 1: Compra 10 unidades
        response = self.client.post('/api/mock/stock/reservar/', {
            "idCompra": "MULTI-USER-001",
            "usuarioId": usuario1_id,
            "productos": [{"idProducto": self.producto1.id, "cantidad": 10}]
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Usuario 2: Compra 15 unidades
        response = self.client.post('/api/mock/stock/reservar/', {
            "idCompra": "MULTI-USER-002",
            "usuarioId": usuario2_id,
            "productos": [{"idProducto": self.producto1.id, "cantidad": 15}]
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Usuario 3: Compra 5 unidades
        response = self.client.post('/api/mock/stock/reservar/', {
            "idCompra": "MULTI-USER-003",
            "usuarioId": usuario3_id,
            "productos": [{"idProducto": self.producto1.id, "cantidad": 5}]
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar stock final
        self.producto1.refresh_from_db()
        stock_esperado = 100 - 10 - 15 - 5  # 70
        self.assertEqual(self.producto1.stock_disponible, stock_esperado)
        
        # Verificar que cada usuario puede ver solo sus reservas
        response = self.client.get(f'/api/mock/stock/reservas/?usuarioId={usuario1_id}')
        self.assertEqual(len(response.json()['data']), 1)
        
        response = self.client.get(f'/api/mock/stock/reservas/?usuarioId={usuario2_id}')
        self.assertEqual(len(response.json()['data']), 1)
    
    def test_flujo_stock_insuficiente_no_crea_envio(self):
        """
        Test E2E: Si no hay stock suficiente, no se debe poder crear envío
        """
        # Intentar reservar más stock del disponible
        response = self.client.post('/api/mock/stock/reservar/', {
            "idCompra": "NO-STOCK-001",
            "usuarioId": 999,
            "productos": [
                {"idProducto": self.producto1.id, "cantidad": 200}  # Solo hay 100
            ]
        }, format='json')
        
        # Debe fallar la reserva
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # El stock no debe haberse modificado
        self.producto1.refresh_from_db()
        self.assertEqual(self.producto1.stock_disponible, 100)
    
    def test_flujo_comparacion_metodos_envio(self):
        """
        Test E2E: Comparar costos entre diferentes métodos de envío
        """
        productos = [
            {"id": self.producto1.id, "quantity": 2},
            {"id": self.producto2.id, "quantity": 1}
        ]
        direccion = {
            "street": "Calle Principal 456",
            "city": "Mendoza",
            "state": "Mendoza",
            "postal_code": "M5500",
            "country": "Argentina"
        }
        
        # Calcular costo con transporte terrestre
        response_road = self.client.post('/api/mock/logistica/calcular-costo/', {
            "delivery_address": direccion,
            "products": productos,
            "transport_type": "road"
        }, format='json')
        self.assertEqual(response_road.status_code, status.HTTP_200_OK)
        costo_road = Decimal(str(response_road.json()['estimated_cost']))
        dias_road = response_road.json()['estimated_delivery_days']
        
        # Calcular costo con express
        response_express = self.client.post('/api/mock/logistica/calcular-costo/', {
            "delivery_address": direccion,
            "products": productos,
            "transport_type": "express"
        }, format='json')
        self.assertEqual(response_express.status_code, status.HTTP_200_OK)
        costo_express = Decimal(str(response_express.json()['estimated_cost']))
        dias_express = response_express.json()['estimated_delivery_days']
        
        # Express debe ser más caro pero más rápido
        self.assertGreater(costo_express, costo_road)
        self.assertLess(dias_express, dias_road)
        
        print(f"\n📊 Comparación de métodos de envío:")
        print(f"   - Terrestre: ${costo_road} ({dias_road} días)")
        print(f"   - Express: ${costo_express} ({dias_express} días)")
    
    def test_flujo_listar_historial_usuario(self):
        """
        Test E2E: Obtener historial completo de un usuario
        """
        usuario_id = 555
        
        # Crear múltiples reservas
        for i in range(3):
            self.client.post('/api/mock/stock/reservar/', {
                "idCompra": f"HIST-{i+1}",
                "usuarioId": usuario_id,
                "productos": [{"idProducto": self.producto1.id, "cantidad": 2}]
            }, format='json')
        
        # Crear múltiples envíos
        for i in range(2):
            self.client.post('/api/mock/logistica/shipping/', {
                "order_id": 5000 + i,
                "user_id": usuario_id,
                "delivery_address": {
                    "street": f"Calle {i}",
                    "city": "Buenos Aires",
                    "state": "CABA",
                    "postal_code": "C1000",
                    "country": "Argentina"
                },
                "transport_type": "road",
                "products": [{"id": self.producto1.id, "quantity": 1}]
            }, format='json')
        
        # Obtener historial de reservas
        response_reservas = self.client.get(f'/api/mock/stock/reservas/?usuarioId={usuario_id}')
        self.assertEqual(response_reservas.status_code, status.HTTP_200_OK)
        reservas = response_reservas.json()['data']
        self.assertEqual(len(reservas), 3)
        
        # Obtener historial de envíos
        response_envios = self.client.get(f'/api/mock/logistica/shipping/?user_id={usuario_id}')
        self.assertEqual(response_envios.status_code, status.HTTP_200_OK)
        envios = response_envios.json()['data']
        self.assertEqual(len(envios), 2)
        
        print(f"\n📋 Historial del usuario {usuario_id}:")
        print(f"   - Reservas: {len(reservas)}")
        print(f"   - Envíos: {len(envios)}")
    
    def test_flujo_cambio_estado_envio(self):
        """
        Test E2E: Verificar que los estados de envío son consistentes
        """
        # Crear reserva y envío
        reserva_payload = {
            "idCompra": "EST-001",
            "usuarioId": 666,
            "productos": [{"idProducto": self.producto1.id, "cantidad": 1}]
        }
        response = self.client.post('/api/mock/stock/reservar/', reserva_payload, format='json')
        id_reserva = response.json()['idReserva']
        
        envio_payload = {
            "order_id": id_reserva,
            "user_id": 666,
            "delivery_address": {
                "street": "Test",
                "city": "Test",
                "state": "Test",
                "postal_code": "12345",
                "country": "Argentina"
            },
            "transport_type": "road",
            "products": [{"id": self.producto1.id, "quantity": 1}]
        }
        response = self.client.post('/api/mock/logistica/shipping/', envio_payload, format='json')
        id_envio = response.json()['shipping_id']
        
        # Verificar estado inicial
        response = self.client.get(f'/api/mock/logistica/shipping/{id_envio}/')
        self.assertEqual(response.json()['estado'], 'PENDIENTE')
        
        # Simular cambio de estado (en un sistema real esto sería automático)
        envio = Envio.objects.get(id=id_envio)
        envio.estado = 'EN_TRANSITO'
        envio.save()
        
        # Verificar cambio
        response = self.client.get(f'/api/mock/logistica/shipping/{id_envio}/')
        self.assertEqual(response.json()['estado'], 'EN_TRANSITO')


class RendimientoAPITestCase(TestCase):
    """Tests de rendimiento y estrés"""
    
    def setUp(self):
        """Crear datos masivos para pruebas de rendimiento"""
        self.client = APIClient()
        
        # Crear categoría
        self.categoria = Categoria.objects.create(
            nombre="Masivo",
            descripcion="Test de carga"
        )
        
        # Crear 50 productos
        self.productos = []
        for i in range(50):
            producto = Producto.objects.create(
                nombre=f"Producto {i+1}",
                descripcion=f"Descripción {i+1}",
                precio=1000.00 + (i * 100),
                stock_disponible=100,
                categoria=self.categoria
            )
            self.productos.append(producto)
        
        # Crear métodos de transporte
        MetodoTransporte.objects.create(
            tipo="road",
            nombre_display="Road",
            descripcion="Test",
            costo_base=500.00,
            dias_entrega_estimados=5
        )
    
    def test_listar_muchos_productos(self):
        """Test: Listar 50 productos sin problemas de rendimiento"""
        response = self.client.get('/api/mock/stock/productos/?limit=50')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 50)
    
    def test_reservar_multiples_productos_simultaneos(self):
        """Test: Reservar 10 productos diferentes en una sola transacción"""
        productos_payload = [
            {"idProducto": p.id, "cantidad": 1}
            for p in self.productos[:10]
        ]
        
        response = self.client.post('/api/mock/stock/reservar/', {
            "idCompra": "BULK-001",
            "usuarioId": 999,
            "productos": productos_payload
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar que se creó una sola reserva con 10 detalles
        reserva = Reserva.objects.get(id_compra="BULK-001")
        self.assertEqual(reserva.detalles.count(), 10)
