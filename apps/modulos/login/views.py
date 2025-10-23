from django.shortcuts import render,redirect 
from django.contrib.auth import authenticate, login,logout
from apps.modulos.administracion.models import Usuario
import logging
log = logging.getLogger("app")

# Create your views here.



def login_view (request):
    
    if request.method == "POST":
        
        email = request.POST.get('gmail')
        contraseña = request.POST.get('contraseña')

        log.info("Intento de login con email=%s", email)

        usuario_login = authenticate(request, email=email, password=contraseña)


        if usuario_login is not None:
            #establece la sesion del usuario autenticado en el sistema 
            login(request, usuario_login,backend='allauth.account.auth_backends.AuthenticationBackend')
            
            return redirect('inicio')
        else:
            log.debug("usuario login: %s", usuario_login)

    #Usuario.objects.all().delete()
    usuario_existente = Usuario.objects.all()

    
    log.debug("usuarios:")
    for i in usuario_existente: 
        log.debug("%s", i)
        log.debug("--------------------------")
    context= {'active_tab': 'login'}




    
    return render(request, "login_registro.html",context)


def registro_view(request):
    if request.method == "POST":
        # Obtengo los datos del nuevo usuario desde el formulario
        email = request.POST.get('gmail')
        usuario = request.POST.get('usuario')
        contraseña = request.POST.get('contraseña')

        log.info("Intento de registro email=%s usuario=%s", email, usuario)
        # Verifico si ya existe un usuario con el mismo nombre
        if Usuario.objects.filter(username=usuario).exists():
            log.warning("Registro: usuario ya existe")
            return render(request, 'login_registro.html', {'error': 'El nombre de usuario ya está registrado.'})

        # Verifico si ya existe un usuario con el mismo correo electrónico
        if Usuario.objects.filter(email=email).exists():
            log.warning("Registro: correo ya existe")
            return render(request, 'login_registro.html', {'error': 'El correo electrónico ya está registrado.'})


        # Creo un nuevo usuario en la base de datos
        nuevo_usuario = Usuario.objects.create_user(username=usuario, email=email, password=contraseña)
        
        # Autentico al usuario después de registrar
        login(request, nuevo_usuario,backend='allauth.account.auth_backends.AuthenticationBackend')
        log.info("Usuario autenticado con éxito")
        return redirect('inicio')

    # Manejar el caso en que el método de solicitud no sea "POST"
    return render(request, 'login_registro.html')

def cerrar_sesion(request):
    logout(request)
    return redirect('inicio')