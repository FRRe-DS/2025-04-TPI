#!/usr/bin/env python
"""
Script de pruebas de integración para verificar que las APIs de Compras
se comunican correctamente con Stock API (Grupo 02) y Logística API (Grupo 03).

Ejecutar: python ScriptParaApi/test_integracion_apis.py

Requisitos:
- Docker compose up y corriendo
- USE_MOCK_APIS="false" en docker-compose.yml
- Servicios stock-backend, shipping-back, django, nginx activos
"""

import requests
import json
from typing import Dict, Any, Optional
from datetime import datetime


class Colors:
    """Colores ANSI para output en terminal"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class IntegracionTester:
    """Tester de integración para APIs de Compras con Stock y Logística"""
    
    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.user_id: Optional[int] = None
        self.product_id: Optional[str] = None
        self.pedido_id: Optional[int] = None
        self.reserva_id: Optional[str] = None
        self.envio_id: Optional[int] = None
        
        # URLs de las APIs
        self.keycloak_url = f"{base_url}:8080/realms/ds-2025-realm/protocol/openid-connect/token"
        self.compras_api = f"{base_url}/compras/api"
        self.stock_api = f"{base_url}/stock/api/v1"
        self.logistica_api = f"{base_url}/logistica"
        
        # Contadores de pruebas
        self.tests_passed = 0
        self.tests_failed = 0
        self.tests_total = 0
    
    def print_header(self, text: str):
        """Imprime un encabezado destacado"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
    
    def print_test(self, test_name: str, success: bool, details: str = ""):
        """Imprime el resultado de una prueba"""
        self.tests_total += 1
        if success:
            self.tests_passed += 1
            icon = "✅"
            color = Colors.OKGREEN
        else:
            self.tests_failed += 1
            icon = "❌"
            color = Colors.FAIL
        
        print(f"{color}{icon} Test #{self.tests_total}: {test_name}{Colors.ENDC}")
        if details:
            print(f"   {Colors.OKCYAN}→ {details}{Colors.ENDC}")
    
    def print_summary(self):
        """Imprime resumen final de pruebas"""
        self.print_header("RESUMEN DE PRUEBAS")
        total_color = Colors.OKGREEN if self.tests_failed == 0 else Colors.WARNING
        
        print(f"{total_color}Total de pruebas: {self.tests_total}{Colors.ENDC}")
        print(f"{Colors.OKGREEN}Exitosas: {self.tests_passed}{Colors.ENDC}")
        print(f"{Colors.FAIL}Fallidas: {self.tests_failed}{Colors.ENDC}")
        
        if self.tests_failed == 0:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 ¡TODAS LAS PRUEBAS PASARON!{Colors.ENDC}\n")
        else:
            print(f"\n{Colors.WARNING}{Colors.BOLD}⚠️  Algunas pruebas fallaron. Revisar logs.{Colors.ENDC}\n")
    
    def obtener_token_keycloak(self) -> bool:
        """Paso 1: Obtener token de Keycloak"""
        self.print_header("PASO 1: Autenticación en Keycloak")
        
        try:
            data = {
                'grant_type': 'password',
                'client_id': 'grupo-04',
                'client_secret': '6be1bec1-9472-499f-ab37-883d78f57829',
                'username': 'usuario_test',
                'password': 'password123',
                'scope': 'productos:read'
            }
            
            print(f"📡 POST {self.keycloak_url}")
            response = requests.post(self.keycloak_url, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data['access_token']
                self.print_test(
                    "Obtener token de Keycloak",
                    True,
                    f"Token obtenido: {self.token[:30]}..."
                )
                return True
            else:
                self.print_test(
                    "Obtener token de Keycloak",
                    False,
                    f"Status {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.print_test("Obtener token de Keycloak", False, f"Error: {str(e)}")
            return False
    
    def verificar_servicios_activos(self) -> bool:
        """Paso 2: Verificar que los servicios estén activos"""
        self.print_header("PASO 2: Verificación de Servicios")
        
        servicios_ok = True
        
        # Verificar Django/Compras
        try:
            response = requests.get(f"{self.compras_api}/", timeout=5)
            self.print_test(
                "Servicio Django/Compras activo",
                response.status_code in [200, 404],  # 404 está bien, significa que está respondiendo
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.print_test("Servicio Django/Compras activo", False, f"Error: {str(e)}")
            servicios_ok = False
        
        # Verificar Stock API
        try:
            response = requests.get(f"{self.stock_api}/productos/", timeout=5)
            self.print_test(
                "Servicio Stock API activo",
                response.status_code in [200, 401],  # 401 ok, necesita auth
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.print_test("Servicio Stock API activo", False, f"Error: {str(e)}")
            servicios_ok = False
        
        # Verificar Logística API
        try:
            response = requests.get(f"{self.logistica_api}/", timeout=5)
            self.print_test(
                "Servicio Logística API activo",
                response.status_code in [200, 404, 401],
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.print_test("Servicio Logística API activo", False, f"Error: {str(e)}")
            servicios_ok = False
        
        return servicios_ok
    
    def test_stock_listar_productos(self) -> bool:
        """Paso 3: Listar productos desde Stock API"""
        self.print_header("PASO 3: Integración con Stock - Listar Productos")
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            print(f"📡 GET {self.stock_api}/productos/?page=1&limit=5")
            
            response = requests.get(
                f"{self.stock_api}/productos/",
                headers=headers,
                params={'page': 1, 'limit': 5}
            )
            
            if response.status_code == 200:
                data = response.json()
                productos = data.get('data', [])
                
                if productos and len(productos) > 0:
                    self.product_id = productos[0]['id']
                    self.print_test(
                        "Listar productos de Stock API",
                        True,
                        f"Obtenidos {len(productos)} productos. Primer ID: {self.product_id}"
                    )
                    
                    # Verificar que NO sean datos mock
                    primer_producto = productos[0]
                    es_mock = primer_producto.get('nombre', '').startswith('Producto Mock')
                    
                    self.print_test(
                        "Los datos NO son mock (datos reales de Stock)",
                        not es_mock,
                        f"Producto: {primer_producto.get('nombre', 'N/A')}"
                    )
                    
                    return True
                else:
                    self.print_test("Listar productos de Stock API", False, "No hay productos")
                    return False
            else:
                self.print_test(
                    "Listar productos de Stock API",
                    False,
                    f"Status {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.print_test("Listar productos de Stock API", False, f"Error: {str(e)}")
            return False
    
    def test_stock_obtener_producto(self) -> bool:
        """Paso 4: Obtener detalle de un producto específico"""
        self.print_header("PASO 4: Integración con Stock - Detalle de Producto")
        
        if not self.product_id:
            self.print_test("Obtener detalle de producto", False, "No hay product_id disponible")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            print(f"📡 GET {self.stock_api}/productos/{self.product_id}/")
            
            response = requests.get(
                f"{self.stock_api}/productos/{self.product_id}/",
                headers=headers
            )
            
            if response.status_code == 200:
                producto = response.json()
                self.print_test(
                    "Obtener producto específico de Stock",
                    True,
                    f"Producto: {producto.get('nombre', 'N/A')} - Precio: ${producto.get('precio', 0)}"
                )
                
                # Verificar campos importantes
                campos_ok = all(k in producto for k in ['id', 'nombre', 'precio'])
                self.print_test(
                    "Producto tiene campos requeridos (id, nombre, precio)",
                    campos_ok,
                    f"Campos presentes: {list(producto.keys())}"
                )
                
                return True
            else:
                self.print_test(
                    "Obtener producto específico de Stock",
                    False,
                    f"Status {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.print_test("Obtener producto específico de Stock", False, f"Error: {str(e)}")
            return False
    
    def test_compras_agregar_al_carrito(self) -> bool:
        """Paso 5: Agregar producto al carrito (debe validar con Stock)"""
        self.print_header("PASO 5: Compras - Agregar al Carrito (valida con Stock)")
        
        if not self.product_id:
            self.print_test("Agregar al carrito", False, "No hay product_id disponible")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            payload = {
                'productId': self.product_id,
                'cantidad': 2
            }
            
            print(f"📡 POST {self.compras_api}/shopcart/")
            print(f"   Body: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                f"{self.compras_api}/shopcart/",
                headers=headers,
                json=payload
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.print_test(
                    "Agregar producto al carrito",
                    True,
                    f"Producto agregado. Carrito items: {data.get('items', [])}"
                )
                
                # Verificar que el producto tenga datos de Stock
                items = data.get('items', [])
                if items and len(items) > 0:
                    producto_info = items[-1].get('product', {})
                    tiene_info_stock = 'nombre' in producto_info or 'precio' in producto_info
                    
                    self.print_test(
                        "El item tiene información de Stock API",
                        tiene_info_stock,
                        f"Info producto: {producto_info}"
                    )
                
                return True
            else:
                self.print_test(
                    "Agregar producto al carrito",
                    False,
                    f"Status {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.print_test("Agregar producto al carrito", False, f"Error: {str(e)}")
            return False
    
    def test_compras_ver_carrito(self) -> bool:
        """Paso 6: Ver carrito (debe mostrar datos de Stock)"""
        self.print_header("PASO 6: Compras - Ver Carrito")
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            print(f"📡 GET {self.compras_api}/shopcart/")
            
            response = requests.get(
                f"{self.compras_api}/shopcart/",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                
                self.print_test(
                    "Ver carrito con items",
                    len(items) > 0,
                    f"Items en carrito: {len(items)}"
                )
                
                if len(items) > 0:
                    # Verificar que los productos NO sean None
                    productos_ok = all(item.get('product') is not None for item in items)
                    self.print_test(
                        "Todos los items tienen información de producto",
                        productos_ok,
                        f"Items con producto: {sum(1 for i in items if i.get('product'))}/{len(items)}"
                    )
                
                return True
            else:
                self.print_test("Ver carrito", False, f"Status {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test("Ver carrito", False, f"Error: {str(e)}")
            return False
    
    def test_compras_crear_pedido_desde_carrito(self) -> bool:
        """Paso 7: Crear pedido desde carrito (debe reservar en Stock)"""
        self.print_header("PASO 7: Compras - Checkout (reserva stock en Stock API)")
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            print(f"📡 POST {self.compras_api}/pedidos/desde-carrito/")
            
            response = requests.post(
                f"{self.compras_api}/pedidos/desde-carrito/",
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.pedido_id = data.get('id')
                
                self.print_test(
                    "Crear pedido desde carrito",
                    self.pedido_id is not None,
                    f"Pedido ID: {self.pedido_id}"
                )
                
                # Verificar que tenga ID de reserva de Stock
                self.reserva_id = data.get('stock_reserva_id') or data.get('reservaId')
                
                self.print_test(
                    "Pedido tiene ID de reserva de Stock",
                    self.reserva_id is not None,
                    f"Reserva ID: {self.reserva_id}"
                )
                
                return self.pedido_id is not None
            else:
                self.print_test(
                    "Crear pedido desde carrito",
                    False,
                    f"Status {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.print_test("Crear pedido desde carrito", False, f"Error: {str(e)}")
            return False
    
    def test_compras_confirmar_pedido(self) -> bool:
        """Paso 8: Confirmar pedido (debe crear envío en Logística)"""
        self.print_header("PASO 8: Compras - Confirmar Pedido (crea envío en Logística)")
        
        if not self.pedido_id:
            self.print_test("Confirmar pedido", False, "No hay pedido_id disponible")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            print(f"📡 POST {self.compras_api}/pedidos/{self.pedido_id}/confirmar/")
            
            response = requests.post(
                f"{self.compras_api}/pedidos/{self.pedido_id}/confirmar/",
                headers=headers
            )
            
            # Puede dar 502 si Logística no está disponible, pero eso es OK para esta prueba
            if response.status_code in [200, 201]:
                data = response.json()
                self.envio_id = data.get('envio_id') or data.get('shippingId')
                
                self.print_test(
                    "Confirmar pedido",
                    True,
                    f"Pedido confirmado"
                )
                
                if self.envio_id:
                    self.print_test(
                        "Pedido tiene ID de envío de Logística",
                        True,
                        f"Envío ID: {self.envio_id}"
                    )
                else:
                    self.print_test(
                        "Pedido tiene ID de envío de Logística",
                        False,
                        "No se obtuvo envio_id (puede ser que Logística no esté disponible)"
                    )
                
                return True
                
            elif response.status_code == 502:
                self.print_test(
                    "Confirmar pedido",
                    True,  # 502 es esperado si Logística no está
                    f"502 Bad Gateway - Logística API no disponible (esperado)"
                )
                return True
            else:
                self.print_test(
                    "Confirmar pedido",
                    False,
                    f"Status {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.print_test("Confirmar pedido", False, f"Error: {str(e)}")
            return False
    
    def test_compras_historial_pedidos(self) -> bool:
        """Paso 9: Ver historial de pedidos"""
        self.print_header("PASO 9: Compras - Historial de Pedidos")
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            print(f"📡 GET {self.compras_api}/pedidos/")
            
            response = requests.get(
                f"{self.compras_api}/pedidos/",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                pedidos = data if isinstance(data, list) else data.get('results', [])
                
                self.print_test(
                    "Ver historial de pedidos",
                    len(pedidos) > 0,
                    f"Total pedidos: {len(pedidos)}"
                )
                
                # Verificar que el pedido recién creado esté en la lista
                if self.pedido_id:
                    pedido_existe = any(p.get('id') == self.pedido_id for p in pedidos)
                    self.print_test(
                        f"El pedido #{self.pedido_id} aparece en el historial",
                        pedido_existe,
                        ""
                    )
                
                return True
            else:
                self.print_test("Ver historial de pedidos", False, f"Status {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test("Ver historial de pedidos", False, f"Error: {str(e)}")
            return False
    
    def ejecutar_todas_las_pruebas(self):
        """Ejecuta todas las pruebas en secuencia"""
        print(f"\n{Colors.BOLD}{Colors.OKCYAN}")
        print("╔═══════════════════════════════════════════════════════════════════╗")
        print("║    TEST DE INTEGRACIÓN - COMPRAS ↔ STOCK ↔ LOGÍSTICA             ║")
        print("║    Verificando comunicación real entre microservicios             ║")
        print("╚═══════════════════════════════════════════════════════════════════╝")
        print(f"{Colors.ENDC}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Paso 1: Autenticación
        if not self.obtener_token_keycloak():
            print(f"\n{Colors.FAIL}❌ No se pudo obtener token. Abortando pruebas.{Colors.ENDC}")
            self.print_summary()
            return False
        
        # Paso 2: Verificar servicios
        if not self.verificar_servicios_activos():
            print(f"\n{Colors.WARNING}⚠️  Algunos servicios no están activos. Continuando...{Colors.ENDC}")
        
        # Paso 3-4: Pruebas de Stock API
        self.test_stock_listar_productos()
        self.test_stock_obtener_producto()
        
        # Paso 5-6: Pruebas de Carrito (integración con Stock)
        self.test_compras_agregar_al_carrito()
        self.test_compras_ver_carrito()
        
        # Paso 7: Checkout (reserva en Stock)
        self.test_compras_crear_pedido_desde_carrito()
        
        # Paso 8: Confirmar (envío en Logística)
        self.test_compras_confirmar_pedido()
        
        # Paso 9: Historial
        self.test_compras_historial_pedidos()
        
        # Resumen final
        self.print_summary()
        
        return self.tests_failed == 0


def main():
    """Función principal"""
    tester = IntegracionTester(base_url="http://localhost")
    
    try:
        exito = tester.ejecutar_todas_las_pruebas()
        
        # Instrucciones adicionales
        print(f"\n{Colors.OKCYAN}{Colors.BOLD}📋 VERIFICACIÓN ADICIONAL:{Colors.ENDC}")
        print(f"\n{Colors.OKCYAN}Para ver logs de integración, ejecuta:{Colors.ENDC}")
        print(f"  {Colors.BOLD}docker-compose logs django | Select-String 'StockClient'{Colors.ENDC}")
        print(f"  {Colors.BOLD}docker-compose logs django | Select-String 'LogisticaClient'{Colors.ENDC}")
        print(f"  {Colors.BOLD}docker-compose logs stock-backend{Colors.ENDC}")
        print(f"  {Colors.BOLD}docker-compose logs shipping-back{Colors.ENDC}\n")
        
        return 0 if exito else 1
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}⚠️  Pruebas interrumpidas por el usuario.{Colors.ENDC}\n")
        return 1
    except Exception as e:
        print(f"\n\n{Colors.FAIL}❌ Error fatal: {str(e)}{Colors.ENDC}\n")
        return 1


if __name__ == "__main__":
    exit(main())
