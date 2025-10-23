from django.urls import path
from django.shortcuts import render
from apps.modulos.login.views import login_view, registro_view, cerrar_sesion
from . import views

# vista mínima para renderizar index.html
def index_view(request):
    return render(request, "login/index.html")

app_name = "login"

urlpatterns = [

    path('index/', index_view, name="index"),
    path('login/', login_view, name="login"),
    path('registro/', registro_view, name='registro'),
    path('cerrar-sesion/', views.cerrar_sesion, name='cerrar_sesion'),
]

