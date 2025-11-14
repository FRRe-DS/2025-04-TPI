# tu_app/adapters.py

import logging

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model


log = logging.getLogger("keycloak")

User = get_user_model()

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Este método se llama justo antes de que se cree la cuenta social
        # o se inicie el proceso de login con la cuenta social.
        
        # Verifica si el email obtenido desde el proveedor social ya existe
        # en alguna cuenta local.
        email = None
        # Dependiendo del proveedor (por ejemplo Keycloak) el email se puede obtener así:
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

    def on_authentication_error(
        self,
        request,
        provider,
        error=None,
        exception=None,
        extra_context=None,
    ):
        if provider.id == "keycloak":
            detalles = []
            if error:
                detalles.append(f"error={error}")
            if request is not None:
                for key in ("error_description", "state", "iss"):
                    valor = request.GET.get(key)
                    if valor:
                        detalles.append(f"{key}={valor}")
            if exception and isinstance(exception, Exception):
                log.error(
                    "Keycloak devolvió una respuesta de error durante el login: %s",
                    "; ".join(detalles) or "sin detalles",
                    exc_info=exception,
                )
            else:
                log.error(
                    "Keycloak devolvió una respuesta de error durante el login: %s",
                    "; ".join(detalles) or "sin detalles",
                )

        return super().on_authentication_error(
            request,
            provider,
            error=error,
            exception=exception,
            extra_context=extra_context,
        )
