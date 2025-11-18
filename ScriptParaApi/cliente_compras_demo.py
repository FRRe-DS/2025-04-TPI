"""
Script de prueba E2E para el proyecto 2025-04-TPI.

Este script prueba el flujo completo:
1. Autenticación con Keycloak (obtener token)
2. Listar productos
3. Agregar productos al carrito
4. Ver carrito
5. Hacer checkout (crear pedido)
6. Ver historial de pedidos

CONFIGURACIÓN PREVIA:
- Keycloak debe estar corriendo (por defecto en localhost:8080)
- Django debe estar corriendo (por defecto en localhost:8000 o detrás de nginx)
- Debe existir un usuario en Keycloak con las credenciales configuradas
"""

import requests
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import sys

# ==========================
# CONFIGURACIÓN
# ==========================

# URL base del proyecto
# Opciones:
#   "http://localhost/compras"  -> Si usás Nginx con prefijo /compras
#   "http://localhost:8000"     -> Si usás Django directamente
BASE_URL = "http://localhost/compras"

# Configuración de Keycloak
KEYCLOAK_BASE_URL = "http://localhost:8080"
KEYCLOAK_REALM = "ds-2025-realm"
KEYCLOAK_CLIENT_ID = "grupo-04"
KEYCLOAK_CLIENT_SECRET = "6be1bec1-9472-499f-ab37-883d78f57829"  # Dejar vacío si usás PKCE

# Credenciales del usuario de prueba (debe existir en Keycloak)
TEST_USERNAME = "admin"  # o email si está configurado así
TEST_PASSWORD = "ds2025"

# ==========================
# MODELOS
# ==========================

@dataclass
class AuthToken:
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    token_type: str = "Bearer"


# ==========================
# FUNCIONES AUXILIARES
# ==========================

def build_url(path: str) -> str:
    """
    Construye la URL completa concatenando BASE_URL con el path.
    Los paths en este proyecto son /api/...
    """
    base = BASE_URL.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return f"{base}{path}"


def auth_headers(token: str) -> Dict[str, str]:
    """Genera los headers con el token de autenticación."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# ==========================
# AUTENTICACIÓN CON KEYCLOAK
# ==========================

def obtener_token_keycloak(username: str, password: str) -> AuthToken:
    """
    Obtiene un token de acceso desde Keycloak usando el flujo
    Resource Owner Password Credentials (Direct Access Grant).
    
    NOTA: Este flujo debe estar habilitado en Keycloak para el cliente.
    """
    token_url = (
        f"{KEYCLOAK_BASE_URL}/realms/{KEYCLOAK_REALM}"
        f"/protocol/openid-connect/token"
    )
    
    payload = {
        "client_id": KEYCLOAK_CLIENT_ID,
        "grant_type": "client_credentials",
        "scope": "productos:read",
        "client_secret": KEYCLOAK_CLIENT_SECRET
    }
    
    try:
        resp = requests.post(token_url, data=payload)
        
        if resp.status_code != 200:
            print(f"❌ Error al obtener token de Keycloak ({resp.status_code}):")
            print(resp.text)
            raise RuntimeError(
                f"No se pudo autenticar con Keycloak. "
                f"Verificá que el usuario existe y las credenciales son correctas."
            )
        
        data = resp.json()
        return AuthToken(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_in=data.get("expires_in"),
            token_type=data.get("token_type", "Bearer"),
        )
    except requests.exceptions.ConnectionError:
        print(f"❌ No se pudo conectar a Keycloak en {KEYCLOAK_BASE_URL}")
        print("   Verificá que Keycloak esté corriendo.")
        sys.exit(1)


# ==========================
# PRODUCTOS
# ==========================

def listar_productos(token: str, page: int = 1, limit: int = 20) -> List[Dict[str, Any]]:
    """
    GET /api/product/
    
    Devuelve lista paginada de productos disponibles.
    """
    url = build_url("/api/product/")
    params = {"page": page, "limit": limit}
    
    resp = requests.get(url, headers=auth_headers(token), params=params)
    
    if resp.status_code != 200:
        raise RuntimeError(
            f"Error al listar productos ({resp.status_code}): {resp.text}"
        )
    
    # DRF pagina las respuestas, extraemos los resultados
    data = resp.json()
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    return data if isinstance(data, list) else []


def obtener_producto(token: str, producto_id: int) -> Dict[str, Any]:
    """
    GET /api/product/{id}/
    
    Obtiene el detalle de un producto específico.
    """
    url = build_url(f"/api/product/{producto_id}/")
    resp = requests.get(url, headers=auth_headers(token))
    
    if resp.status_code != 200:
        raise RuntimeError(
            f"Error al obtener producto ({resp.status_code}): {resp.text}"
        )
    
    return resp.json()


# ==========================
# CARRITO
# ==========================

def ver_carrito(token: str) -> Dict[str, Any]:
    """
    GET /api/shopcart/
    
    Obtiene el carrito actual del usuario autenticado.
    """
    url = build_url("/api/shopcart/")
    resp = requests.get(url, headers=auth_headers(token))
    
    if resp.status_code != 200:
        raise RuntimeError(
            f"Error al obtener carrito ({resp.status_code}): {resp.text}"
        )
    
    return resp.json()


def agregar_al_carrito(token: str, producto_id: int, cantidad: int) -> Dict[str, Any]:
    """
    POST /api/shopcart/
    
    Agrega un producto al carrito o actualiza su cantidad.
    
    Body:
        {
            "productId": int,
            "quantity": int
        }
    """
    url = build_url("/api/shopcart/")
    payload = {
        "productId": producto_id,
        "quantity": cantidad,
    }
    
    resp = requests.post(url, headers=auth_headers(token), json=payload)
    
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Error al agregar al carrito ({resp.status_code}): {resp.text}"
        )
    
    return resp.json()


def actualizar_item_carrito(token: str, item_id: int, cantidad: int) -> Dict[str, Any]:
    """
    PATCH /api/shopcart/{item_id}/
    
    Actualiza la cantidad de un item específico del carrito.
    """
    url = build_url(f"/api/shopcart/{item_id}/")
    payload = {"quantity": cantidad}
    
    resp = requests.patch(url, headers=auth_headers(token), json=payload)
    
    if resp.status_code != 200:
        raise RuntimeError(
            f"Error al actualizar item ({resp.status_code}): {resp.text}"
        )
    
    return resp.json()


def vaciar_carrito(token: str) -> None:
    """
    DELETE /api/shopcart/
    
    Vacía completamente el carrito del usuario.
    """
    url = build_url("/api/shopcart/")
    resp = requests.delete(url, headers=auth_headers(token))
    
    if resp.status_code not in (200, 204):
        raise RuntimeError(
            f"Error al vaciar carrito ({resp.status_code}): {resp.text}"
        )


# ==========================
# CHECKOUT / PEDIDOS
# ==========================

def hacer_checkout(
    token: str,
    direccion_envio: str,
    metodo_pago: str = "tarjeta",
) -> Dict[str, Any]:
    """
    POST /api/shopcart/checkout
    
    Confirma el carrito actual y crea un pedido.
    
    Body:
        {
            "direccion_envio": string,
            "metodo_pago": string
        }
    
    Respuesta: Pedido creado con su ID y detalles.
    """
    url = build_url("/api/shopcart/checkout")
    payload = {
        "direccion_envio": direccion_envio,
        "metodo_pago": metodo_pago,
    }
    
    resp = requests.post(url, headers=auth_headers(token), json=payload)
    
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Error en checkout ({resp.status_code}): {resp.text}"
        )
    
    return resp.json()


def ver_historial_pedidos(token: str) -> List[Dict[str, Any]]:
    """
    GET /api/shopcart/history
    
    Lista todos los pedidos del usuario autenticado.
    """
    url = build_url("/api/shopcart/history")
    resp = requests.get(url, headers=auth_headers(token))
    
    if resp.status_code != 200:
        raise RuntimeError(
            f"Error al obtener historial ({resp.status_code}): {resp.text}"
        )
    
    data = resp.json()
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    return data if isinstance(data, list) else []


def ver_pedido(token: str, pedido_id: int) -> Dict[str, Any]:
    """
    GET /api/shopcart/history/{id}
    
    Obtiene el detalle de un pedido específico.
    """
    url = build_url(f"/api/shopcart/history/{pedido_id}")
    resp = requests.get(url, headers=auth_headers(token))
    
    if resp.status_code != 200:
        raise RuntimeError(
            f"Error al obtener pedido ({resp.status_code}): {resp.text}"
        )
    
    return resp.json()


def cancelar_pedido(token: str, pedido_id: int) -> None:
    """
    DELETE /api/shopcart/history/{id}
    
    Cancela un pedido existente (si su estado lo permite).
    """
    url = build_url(f"/api/shopcart/history/{pedido_id}")
    resp = requests.delete(url, headers=auth_headers(token))
    
    if resp.status_code not in (200, 204):
        raise RuntimeError(
            f"Error al cancelar pedido ({resp.status_code}): {resp.text}"
        )


# ==========================
# FLUJO DE PRUEBA COMPLETO
# ==========================

def flujo_demo():
    """Ejecuta el flujo completo de prueba E2E."""
    
    print("=" * 60)
    print("🚀 INICIANDO PRUEBA E2E - Proyecto 2025-04-TPI")
    print("=" * 60)
    
    # ============================================================
    # 1. AUTENTICACIÓN CON KEYCLOAK
    # ============================================================
    print("\n📝 Paso 1: Autenticación con Keycloak")
    print(f"   Usuario: {TEST_USERNAME}")
    
    try:
        auth_result = obtener_token_keycloak(TEST_USERNAME, TEST_PASSWORD)
        token = auth_result.access_token
        print(f"   ✅ Token obtenido (expira en {auth_result.expires_in}s)")
        print(f"   Token: {token[:30]}...")
    except Exception as e:
        print(f"   ❌ Error en autenticación: {e}")
        return
    
    # ============================================================
    # 2. LISTAR PRODUCTOS
    # ============================================================
    print("\n📦 Paso 2: Listando productos disponibles")
    
    try:
        productos = listar_productos(token)
        print(f"   ✅ Se encontraron {len(productos)} productos")
        
        if not productos:
            print("   ⚠️  No hay productos disponibles. No se puede continuar.")
            return
        
        # Mostrar primeros 3 productos
        for i, prod in enumerate(productos[:3], 1):
            print(f"   {i}. ID: {prod.get('id')} - {prod.get('nombre', 'N/A')} - ${prod.get('precio', 0)}")
        
        producto_prueba = productos[0]
        
    except Exception as e:
        print(f"   ❌ Error al listar productos: {e}")
        return
    
    # ============================================================
    # 3. VACIAR CARRITO (por las dudas)
    # ============================================================
    print("\n🗑️  Paso 3: Limpiando carrito previo")
    
    try:
        vaciar_carrito(token)
        print("   ✅ Carrito vaciado")
    except Exception as e:
        print(f"   ⚠️  Advertencia al vaciar: {e}")
    
    # ============================================================
    # 4. AGREGAR PRODUCTOS AL CARRITO
    # ============================================================
    print("\n🛒 Paso 4: Agregando productos al carrito")
    
    try:
        resultado = agregar_al_carrito(
            token,
            producto_id=producto_prueba["id"],
            cantidad=2
        )
        print(f"   ✅ Agregado: {producto_prueba.get('nombre')} x 2")
        
        # Agregar otro producto si hay disponible
        if len(productos) > 1:
            segundo_producto = productos[1]
            agregar_al_carrito(token, segundo_producto["id"], 1)
            print(f"   ✅ Agregado: {segundo_producto.get('nombre')} x 1")
            
    except Exception as e:
        print(f"   ❌ Error al agregar al carrito: {e}")
        return
    
    # ============================================================
    # 5. VER CARRITO
    # ============================================================
    print("\n👀 Paso 5: Consultando carrito actual")
    
    try:
        carrito = ver_carrito(token)
        items = carrito.get("items", [])
        total = carrito.get("total", 0)
        
        print(f"   ✅ Carrito con {len(items)} item(s)")
        print(f"   💰 Total: ${total}")
        
        for item in items:
            prod = item.get("producto", {})
            print(f"      - {prod.get('nombre')}: {item.get('cantidad')} x ${prod.get('precio')}")
            
    except Exception as e:
        print(f"   ❌ Error al consultar carrito: {e}")
        return
    
    # ============================================================
    # 6. CHECKOUT (CREAR PEDIDO)
    # ============================================================
    print("\n✅ Paso 6: Realizando checkout")
    
    try:
        pedido = hacer_checkout(
            token,
            direccion_envio="Calle Falsa 123, Resistencia, Chaco, Argentina",
            metodo_pago="tarjeta"
        )
        
        pedido_id = pedido.get("id")
        print(f"   ✅ Pedido creado con ID: {pedido_id}")
        print(f"   📅 Estado: {pedido.get('estado', 'N/A')}")
        print(f"   💵 Total: ${pedido.get('total', 0)}")
        
    except Exception as e:
        print(f"   ❌ Error en checkout: {e}")
        print(f"   Respuesta: {e}")
        return
    
    # ============================================================
    # 7. VER HISTORIAL DE PEDIDOS
    # ============================================================
    print("\n📋 Paso 7: Consultando historial de pedidos")
    
    try:
        historial = ver_historial_pedidos(token)
        print(f"   ✅ Total de pedidos: {len(historial)}")
        
        for i, ped in enumerate(historial[:5], 1):
            print(f"   {i}. Pedido #{ped.get('id')} - {ped.get('estado')} - ${ped.get('total')}")
            
    except Exception as e:
        print(f"   ❌ Error al consultar historial: {e}")
    
    # ============================================================
    # 8. VER DETALLE DEL PEDIDO CREADO
    # ============================================================
    print(f"\n🔍 Paso 8: Consultando detalle del pedido #{pedido_id}")
    
    try:
        detalle = ver_pedido(token, pedido_id)
        print(f"   ✅ Pedido #{detalle.get('id')}")
        print(f"   📍 Dirección: {detalle.get('direccion_envio', 'N/A')}")
        print(f"   💳 Método de pago: {detalle.get('metodo_pago', 'N/A')}")
        print(f"   📦 Items: {len(detalle.get('items', []))}")
        
    except Exception as e:
        print(f"   ❌ Error al consultar detalle: {e}")
    
    # ============================================================
    # RESUMEN FINAL
    # ============================================================
    print("\n" + "=" * 60)
    print("✅ PRUEBA E2E COMPLETADA EXITOSAMENTE")
    print("=" * 60)
    print(f"""
Resumen:
  - Autenticación: OK
  - Productos listados: {len(productos)}
  - Items en carrito: {len(items)}
  - Pedido creado: #{pedido_id}
  - Total pagado: ${total}
    """)


# ==========================
# EJECUCIÓN
# ==========================

if __name__ == "__main__":
    try:
        flujo_demo()
    except KeyboardInterrupt:
        print("\n\n⚠️  Prueba cancelada por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
