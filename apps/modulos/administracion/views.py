from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone


# =======================
#   Función auxiliar
# =======================
def _dashboard_context():
    """
    Devuelve datos de ejemplo para mostrar en el panel de administración.
    Podés reemplazar esto con tus datos reales cuando conectes el backend.
    """
    now = timezone.now()
    return {
        "kpi_ingresos": "1.250.000",
        "kpi_usuarios_nuevos": 42,
        "kpi_items": 318,
        "kpi_ordenes_ok": 289,
        "ultimas_transacciones": [
            {"id": 1021, "usuario": "maxi.v", "monto": "18.200", "fecha": now, "estado": "OK"},
            {"id": 1020, "usuario": "anap", "monto": "7.950", "fecha": now, "estado": "PENDIENTE"},
            {"id": 1019, "usuario": "jps", "monto": "3.100", "fecha": now, "estado": "ERROR"},
        ],
    }


# =======================
#   Vistas principales
# =======================

def administracion_view(request):
    """
    Vista principal del panel de administración.
    """
    # Si querés exigir login, descomentá esto:
    # if not request.user.is_authenticated:
    #     return redirect('login')

    ctx = _dashboard_context()
    return render(request, 'inicio_admin.html', ctx)


# =======================
#   Placeholders (para que no tire NoReverseMatch)
# =======================

def admin_items_nuevo(request):
    """
    Placeholder de 'Nuevo ítem'. 
    Más adelante reemplazalo por tu formulario real.
    """
    ctx = _dashboard_context()
    return render(request, 'inicio_admin.html', ctx)


def admin_reportes(request):
    """
    Placeholder de Reportes.
    """
    ctx = _dashboard_context()
    return render(request, 'inicio_admin.html', ctx)


def admin_config(request):
    """
    Placeholder de Configuración.
    """
    ctx = _dashboard_context()
    return render(request, 'inicio_admin.html', ctx)


def admin_transacciones(request):
    """
    Placeholder de Transacciones.
    """
    ctx = _dashboard_context()
    return render(request, 'inicio_admin.html', ctx)

