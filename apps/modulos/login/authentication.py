from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import jwt
from jwt import PyJWKClient

from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import authentication, exceptions


log = logging.getLogger("keycloak-auth")
_JWK_CLIENT = PyJWKClient(settings.KEYCLOAK_JWKS_URL)


class KeycloakJWTAuthentication(authentication.BaseAuthentication):
    """Autenticación DRF basada en tokens JWT emitidos por Keycloak."""

    keyword = "Bearer"

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode("utf-8")
        if not header:
            return None

        parts = header.split()
        if len(parts) != 2 or parts[0].lower() != self.keyword.lower():
            raise exceptions.AuthenticationFailed("Cabecera Authorization inválida.")

        token = parts[1]
        decoded = self._decode_token(token)
        user = self._get_or_create_user(decoded)
        request.keycloak_token = decoded  # type: ignore[attr-defined]
        return (user, token)

    def authenticate_header(self, request):
        return f'{self.keyword} realm="Keycloak"'

    def _decode_token(self, token: str) -> Dict[str, Any]:
        try:
            signing_key = _JWK_CLIENT.get_signing_key_from_jwt(token)
            decode_kwargs: Dict[str, Any] = {
                "algorithms": ["RS256"],
                "issuer": settings.KEYCLOAK_SERVER_URL.rstrip("/"),
            }
            audience = getattr(settings, "KEYCLOAK_EXPECTED_AUDIENCE", None)
            if audience:
                decode_kwargs["audience"] = audience
            else:
                decode_kwargs["options"] = {"verify_aud": False}
            return jwt.decode(token, signing_key.key, **decode_kwargs)
        except jwt.ExpiredSignatureError as exc:
            log.info("Token expirado recibido desde Keycloak.")
            raise exceptions.AuthenticationFailed("Token expirado.") from exc
        except jwt.InvalidTokenError as exc:
            log.info("Token inválido recibido desde Keycloak: %s", exc)
            raise exceptions.AuthenticationFailed("Token inválido.") from exc

    def _get_or_create_user(self, claims: Dict[str, Any]):
        username = (
            claims.get("preferred_username")
            or claims.get("email")
            or claims.get("sub")
            or claims.get("client_id")
        )
        if not username:
            raise exceptions.AuthenticationFailed("El token no contiene un identificador de usuario.")

        defaults: Dict[str, Any] = {}
        email = claims.get("email")
        if email:
            defaults["email"] = email

        UserModel = get_user_model()
        user, created = UserModel.objects.get_or_create(username=username, defaults=defaults)
        updated_fields = []

        if email and user.email != email:
            user.email = email
            updated_fields.append("email")

        first_name = claims.get("given_name")
        last_name = claims.get("family_name")
        if first_name is not None and user.first_name != first_name:
            user.first_name = first_name
            updated_fields.append("first_name")
        if last_name is not None and user.last_name != last_name:
            user.last_name = last_name
            updated_fields.append("last_name")

        if created:
            user.set_unusable_password()
            user.save(update_fields=["password"])

        if updated_fields:
            safe_fields = [field for field in set(updated_fields) if hasattr(user, field)]
            if safe_fields:
                user.save(update_fields=safe_fields)

        return user
