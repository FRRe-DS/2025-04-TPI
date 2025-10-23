"""
Script para crear datos de prueba en la base de datos
Ejecuta este script después de hacer las migraciones
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Main.settings')
django.setup()

from apps.apis.stockApi.models import Categoria, Producto, Reserva, DetalleReserva
from apps.apis.logisticaApi.models import MetodoTransporte, Envio, ProductoEnvio
from django.utils import timezone
from decimal import Decimal

def crear_datos_stock():
    """Crear datos de prueba para Stock API"""
    print("\n📦 Creando datos de Stock API...")
    
    # Verificar si ya existen datos
    if Producto.objects.exists():
        print("   ℹ️  Ya existen productos en la BD")
        return
    
    # Crear categorías
    categorias_data = [
        {'nombre': 'Electrónica', 'descripcion': 'Productos electrónicos'},
        {'nombre': 'Ropa', 'descripcion': 'Prendas de vestir'},
        {'nombre': 'Hogar', 'descripcion': 'Artículos para el hogar'},
        {'nombre': 'Deportes', 'descripcion': 'Equipamiento deportivo'},
    ]
    
    categorias = {}
    for cat_data in categorias_data:
        try:
            # Intentar con el campo 'activo' primero
            cat, created = Categoria.objects.get_or_create(
                nombre=cat_data['nombre'],
                defaults={'descripcion': cat_data['descripcion'], 'activo': True}
            )
        except Exception:
            # Si falla, intentar sin el campo 'activo' (para compatibilidad)
            cat, created = Categoria.objects.get_or_create(
                nombre=cat_data['nombre'],
                defaults={'descripcion': cat_data['descripcion']}
            )
        categorias[cat.nombre] = cat
        if created:
            print(f"   ✅ Categoría creada: {cat.nombre}")
    
    # Crear productos
    productos_data = [
        {'nombre': 'Laptop Dell XPS 13', 'descripcion': 'Laptop de alto rendimiento', 'precio': Decimal('1299.99'), 'stock_disponible': 15, 'categoria': 'Electrónica'},
        {'nombre': 'iPhone 15 Pro', 'descripcion': 'Smartphone Apple', 'precio': Decimal('999.00'), 'stock_disponible': 25, 'categoria': 'Electrónica'},
        {'nombre': 'Samsung Galaxy S24', 'descripcion': 'Smartphone Samsung', 'precio': Decimal('849.00'), 'stock_disponible': 30, 'categoria': 'Electrónica'},
        {'nombre': 'iPad Air', 'descripcion': 'Tablet Apple', 'precio': Decimal('599.00'), 'stock_disponible': 20, 'categoria': 'Electrónica'},
        {'nombre': 'AirPods Pro', 'descripcion': 'Auriculares inalámbricos', 'precio': Decimal('249.00'), 'stock_disponible': 50, 'categoria': 'Electrónica'},
        {'nombre': 'Camiseta Nike', 'descripcion': 'Camiseta deportiva', 'precio': Decimal('29.99'), 'stock_disponible': 100, 'categoria': 'Ropa'},
        {'nombre': 'Zapatillas Adidas', 'descripcion': 'Calzado deportivo', 'precio': Decimal('89.99'), 'stock_disponible': 40, 'categoria': 'Ropa'},
        {'nombre': 'Jeans Levis', 'descripcion': 'Pantalón vaquero', 'precio': Decimal('79.99'), 'stock_disponible': 60, 'categoria': 'Ropa'},
        {'nombre': 'Lámpara LED', 'descripcion': 'Iluminación moderna', 'precio': Decimal('39.99'), 'stock_disponible': 35, 'categoria': 'Hogar'},
        {'nombre': 'Cafetera Nespresso', 'descripcion': 'Máquina de café', 'precio': Decimal('199.00'), 'stock_disponible': 15, 'categoria': 'Hogar'},
        {'nombre': 'Bicicleta Mountain Bike', 'descripcion': 'Bici de montaña', 'precio': Decimal('499.00'), 'stock_disponible': 10, 'categoria': 'Deportes'},
        {'nombre': 'Pelota de Fútbol', 'descripcion': 'Balón profesional', 'precio': Decimal('29.99'), 'stock_disponible': 80, 'categoria': 'Deportes'},
        {'nombre': 'Raqueta de Tenis', 'descripcion': 'Raqueta profesional', 'precio': Decimal('149.00'), 'stock_disponible': 25, 'categoria': 'Deportes'},
        {'nombre': 'Mochila deportiva', 'descripcion': 'Mochila multiuso', 'precio': Decimal('49.99'), 'stock_disponible': 45, 'categoria': 'Deportes'},
        {'nombre': 'Smartwatch Samsung', 'descripcion': 'Reloj inteligente', 'precio': Decimal('299.00'), 'stock_disponible': 20, 'categoria': 'Electrónica'},
    ]
    
    for prod_data in productos_data:
        categoria_nombre = prod_data.pop('categoria')
        prod, created = Producto.objects.get_or_create(
            nombre=prod_data['nombre'],
            defaults={
                **prod_data,
                'categoria': categorias[categoria_nombre]
            }
        )
        if created:
            print(f"   ✅ Producto creado: {prod.nombre}")
    
    print(f"   ✅ Total productos en BD: {Producto.objects.count()}")


def crear_datos_logistica():
    """Crear datos de prueba para Logística API"""
    print("\n🚚 Creando datos de Logística API...")
    
    # Verificar si ya existen datos
    if MetodoTransporte.objects.exists():
        print("   ℹ️  Ya existen métodos de transporte en la BD")
        return
    
    # Crear métodos de transporte
    metodos_data = [
        {
            'tipo': 'road',
            'nombre_display': 'Transporte Terrestre',
            'descripcion': 'Envío por carretera',
            'costo_base': Decimal('10.00'),
            'costo_por_producto': Decimal('2.00'),
            'tiempo_estimado_dias': 5,
        },
        {
            'tipo': 'air',
            'nombre_display': 'Transporte Aéreo',
            'descripcion': 'Envío por avión',
            'costo_base': Decimal('50.00'),
            'costo_por_producto': Decimal('10.00'),
            'tiempo_estimado_dias': 2,
        },
        {
            'tipo': 'sea',
            'nombre_display': 'Transporte Marítimo',
            'descripcion': 'Envío por barco',
            'costo_base': Decimal('5.00'),
            'costo_por_producto': Decimal('0.50'),
            'tiempo_estimado_dias': 20,
        },
        {
            'tipo': 'rail',
            'nombre_display': 'Transporte Ferroviario',
            'descripcion': 'Envío por tren',
            'costo_base': Decimal('8.00'),
            'costo_por_producto': Decimal('1.50'),
            'tiempo_estimado_dias': 7,
        },
    ]
    
    for metodo_data in metodos_data:
        metodo, created = MetodoTransporte.objects.get_or_create(
            tipo=metodo_data['tipo'],
            defaults={**metodo_data, 'activo': True}
        )
        if created:
            print(f"   ✅ Método de transporte creado: {metodo.nombre_display}")
    
    print(f"   ✅ Total métodos de transporte: {MetodoTransporte.objects.count()}")


def main():
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║              CREACIÓN DE DATOS DE PRUEBA                          ║
║                   DesarrolloAPP                                   ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        crear_datos_stock()
        crear_datos_logistica()
        
        print("""
╔═══════════════════════════════════════════════════════════════════╗
║                   ✅ DATOS CREADOS EXITOSAMENTE                   ║
╚═══════════════════════════════════════════════════════════════════╝

Resumen:
  📦 Categorías: {categorias}
  📦 Productos: {productos}
  🚚 Métodos de transporte: {metodos}

Próximo paso:
  - Ejecuta: python manage.py runserver
  - Visita: http://127.0.0.1:8000/api/docs/
  - Prueba: python tests/test_apis_mock_completo.py
        """.format(
            categorias=Categoria.objects.count(),
            productos=Producto.objects.count(),
            metodos=MetodoTransporte.objects.count()
        ))
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error al crear datos: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
