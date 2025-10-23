from django.urls import path
from . import views

urlpatterns = [
    # Ruta principal (la que ya tenías)
    path('', views.administracion_view, name='administracion'),

    # --- Rutas placeholder para que no falle el dashboard ---
    path('items/nuevo/', views.administracion_view, name='admin_items_nuevo'),
    path('reportes/', views.administracion_view, name='admin_reportes'),
    path('configuracion/', views.administracion_view, name='admin_config'),
    path('transacciones/', views.administracion_view, name='admin_transacciones'),
]
