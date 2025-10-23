# tu_app/adapters.py

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model

User = get_user_model()

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Este método se llama justo antes de que se cree la cuenta social
        # o se inicie el proceso de login con la cuenta social.
        
        # Verifica si el email obtenido desde el proveedor social ya existe
        # en alguna cuenta local.
        email = None
        # Dependiendo del proveedor (en este caso Google) el email se puede obtener así:
        if sociallogin.account.extra_data and "email" in sociallogin.account.extra_data:
            email = sociallogin.account.extra_data["email"]
        
        if email:
            try:
                user = User.objects.get(email=email)
                # Si ya existe un usuario con ese email, enlazar la cuenta social:
                sociallogin.user = user
            except User.DoesNotExist:
                # Si no existe el usuario, se aplicará el comportamiento por defecto
                #  (crear uno nuevo).
                pass
