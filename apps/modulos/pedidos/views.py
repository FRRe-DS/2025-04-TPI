from django.db.models import Count
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import transaction, models
from django.shortcuts import render, redirect
from django.db.models import Count
from .models import Pedido, DetallePedido

# Esta vista parece ser de otra app, pero la dejamos por si acaso.
# Si no pertenece aquí, podés moverla a la app correspondiente.
def inicio_view(request):
    context = {
        'categorias_destacadas': "prueba",
        'productos_destacados': "prueba",
    }
    return render(request, 'inicio.html', context)


def checkout_view(request):
    """Pantalla de checkout para los pedidos."""
    tipos_envio = [
        {
            "id": "domicilio",
            "nombre": "Envío a domicilio",
            "descripcion": "Recibe tus productos directamente en tu domicilio.",
            "costo": "$5.000",
        },
        {
            "id": "retiro_sucursal",
            "nombre": "Retiro en sucursal",
            "descripcion": "Retira tu pedido en nuestra sucursal más cercana.",
            "costo": "Sin costo",
        },
        {
            "id": "envio_expres",
            "nombre": "Envío exprés",
            "descripcion": "Recibe tu pedido en menos de 24 horas.",
            "costo": "$8.500",
        },
    ]

    context = {
        "tipos_envio": tipos_envio,
    }
    return render(request, "checkout.html", context)

# @login_required
# views.py
from decimal import Decimal
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import render, redirect
from .models import Pedido, DetallePedido

# @login_required
def listar_pedidos(request):
    """
    Muestra una lista de pedidos. En desarrollo, permite sembrar datos de prueba con ?seed=1.
    """
    # Sembrar datos "hardcodeados" en la BD si estamos en DEBUG y llegan con ?seed=1
    if settings.DEBUG and request.GET.get("seed") == "1":
        _seed_demo_pedidos(request.user) # Pasamos el usuario para asociar el pedido
        return redirect(request.path)

    # CAMBIO: el campo es 'usuario' y la fecha es 'creado_en'
    pedidos_base = Pedido.objects.filter(usuario=request.user).order_by('-creado_en')
    estado_solicitado = request.GET.get('estado')
    # CAMBIO: los estados válidos vienen de Pedido.Estado.choices
    estados_validos = {choice[0]: choice[1] for choice in Pedido.Estado.choices}

    if estado_solicitado not in estados_validos:
        estado_solicitado = None

    pedidos = pedidos_base
    if estado_solicitado:
        pedidos = pedidos.filter(estado=estado_solicitado)

    resumen_estados = {clave: 0 for clave in estados_validos.keys()}
    for item in pedidos_base.values('estado').annotate(total=Count('id')):
        resumen_estados[item['estado']] = item['total']
    
    filtros_estado = [
        {
            'clave': clave,
            'etiqueta': estados_validos[clave],
            'cantidad': resumen_estados.get(clave, 0),
        }
        for clave in estados_validos
    ]

    context = {
        'pedidos': pedidos,
        'filtros_estado': filtros_estado,
        'estado_solicitado': estado_solicitado,
        'total_pedidos': pedidos_base.count(),
        'etiqueta_estado': estados_validos.get(estado_solicitado) if estado_solicitado else None,
    }
    return render(request, 'pedidos/listar_pedidos.html', context)


# ✅ NUEVA VISTA PARA LA PANTALLA DE PAGO EXITOSO
#@login_required   <-- Lo dejamos comentado por ahora para poder probarlo
def pago_exitoso(request):
    """
    Muestra la página de confirmación de pago exitoso.
    """
    return render(request, 'pedidos/pago_exitoso.html')

# ✅ NUEVA VISTA PARA LA PANTALLA DE PAGO FALLIDO
# @login_required  <-- Lo dejamos comentado por ahora para poder probarlo
def pago_fallido(request):
    """
    Muestra la página de notificación de pago fallido.
    """
    return render(request, 'pedidos/pago_fallido.html')


def mis_pedidos(request):
    """
    Muestra el historial de pedidos del usuario.
    Utiliza datos hardcodeados para la maquetación.
    """
    # Datos hardcodeados para el diseño
    pedidos_hardcoded = [
        {
            'id': '717-1',
            'fecha': '2025-10-05',
            'total': 850000.90,
            'estado': 'en_proceso',
            'estado_display': 'En proceso',
            'direccion_envio': 'Av siempreviva 123',
            'items': [
                {'nombre': 'Computadora asus', 'cantidad': 2, 'precio': 350000.45},
                {'nombre': 'Xiaomi Smartwatch', 'cantidad': 1, 'precio': 150000.00},
            ],
            'puede_cancelar': True,
        },
        {
            'id': '717-2',
            'fecha': '2025-07-15',
            'total': 600000.00,
            'estado': 'entregado',
            'estado_display': 'Entregado',
            'direccion_envio': 'Av siempreviva 125',
            'items': [
                {'nombre': 'Tablet Huawei', 'cantidad': 1, 'precio': 600000.00},
            ],
            'puede_cancelar': False,
        }
    ]

    # Calculamos el subtotal en la vista
    for pedido in pedidos_hardcoded:
        for item in pedido['items']:
            item['subtotal'] = item['cantidad'] * item['precio']

    context = {
        'pedidos': pedidos_hardcoded,
    }
    return render(request, 'pedidos/mis_pedidos.html', context)


# --- FUNCIONES AUXILIARES PARA DATOS DE PRUEBA ---

def _ensure_demo_user():
    """Crea (o recupera) un usuario 'demo'."""
    User = get_user_model()
    demo_user, created = User.objects.get_or_create(
        username='demo',
        defaults={'email': 'demo@example.com'}
    )
    if created:
        # set_password para no guardar en texto plano
        demo_user.set_password('demo12345')
        demo_user.save()
    return demo_user
@transaction.atomic


@transaction.atomic
def _seed_demo_pedidos(user):
    """Crea datos de prueba (limpiando los anteriores de ese usuario)."""
    if user.username != 'demo':
        demo_user = user
    else:
        demo_user = _ensure_demo_user()

    Pedido.objects.filter(usuario=demo_user).delete()

    # Pedido 1
    p1 = Pedido.objects.create(usuario=demo_user, total=Decimal('45999.90'), estado='pendiente')
    DetallePedido.objects.create(pedido=p1, producto_id=1, nombre_producto='Remera Oversize Negra', cantidad=2, precio_unitario=Decimal('9999.95'))
    DetallePedido.objects.create(pedido=p1, producto_id=2, nombre_producto='Jean Slim Azul', cantidad=1, precio_unitario=Decimal('25999.00'))

    # Pedido 2
    p2 = Pedido.objects.create(usuario=demo_user, total=Decimal('18998.00'), estado='pendiente')
    DetallePedido.objects.create(pedido=p2, producto_id=3, nombre_producto='Buzo Canguro Gris', cantidad=1, precio_unitario=Decimal('12999.00'))
    DetallePedido.objects.create(pedido=p2, producto_id=4, nombre_producto='Medias Deportivas (Pack x3)', cantidad=1, precio_unitario=Decimal('5999.00'))
    
    # Pedido 3
    p3 = Pedido.objects.create(usuario=demo_user, total=Decimal('32999.00'), estado='pendiente')
    DetallePedido.objects.create(pedido=p3, producto_id=5, nombre_producto='Zapatillas Urbanas', cantidad=1, precio_unitario=Decimal('32999.00'))
