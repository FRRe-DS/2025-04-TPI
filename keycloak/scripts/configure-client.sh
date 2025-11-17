#!/bin/sh
set -euo

echo "[keycloak-configurator] Waiting for Keycloak to be ready..."
KEYCLOAK_URL="${KEYCLOAK_URL:-http://keycloak:8080}"
KEYCLOAK_REALM="${KEYCLOAK_REALM:-ds-2025-realm}"

until curl -fsS "${KEYCLOAK_URL}/health/ready" >/dev/null 2>&1; do
    sleep 2
done

/opt/keycloak/bin/kcadm.sh config credentials \
    --server "${KEYCLOAK_URL}" \
    --realm master \
    --user "${KEYCLOAK_ADMIN}" \
    --password "${KEYCLOAK_ADMIN_PASSWORD}"

CLIENT_UUID=$(
    /opt/keycloak/bin/kcadm.sh get clients -r "${KEYCLOAK_REALM}" -q clientId=grupo-04 |
        grep -o '"id" *: *"[^"]*"' |
        head -n1 |
        cut -d'"' -f4
)

if [ -z "${CLIENT_UUID:-}" ]; then
    echo "[keycloak-configurator] No se pudo obtener el ID del cliente grupo-04" >&2
    exit 1
fi

echo "[keycloak-configurator] Actualizando URIs permitidas para grupo-04 (${CLIENT_UUID})"
/opt/keycloak/bin/kcadm.sh update "clients/${CLIENT_UUID}" -r "${KEYCLOAK_REALM}" \
    -s 'rootUrl=http://localhost/compras' \
    -s 'adminUrl=http://localhost/compras/' \
    -s 'baseUrl=/' \
    -s 'redirectUris=["http://localhost/compras/accounts/oidc/keycloak/login/callback/","http://127.0.0.1/compras/accounts/oidc/keycloak/login/callback/"]' \
    -s 'webOrigins=["http://localhost","http://127.0.0.1"]' \
    -s 'attributes.post.logout.redirect.uris=http://localhost/compras/*'

echo "[keycloak-configurator] Configuración completada."
