Pasos para la creacion de un admin usuario:

1. Ingresen al keycloak con 
    *usuario: admin
    *contraseña: ds2025

2. Si estan en una seccion llamada "Master" cambien e ingresen a "ds-2025-realm"

3. Vayan a "Users"

4. Creen un user con las siguientes caracteristicas:
    *Username: admin
    *Email: admin@gmail.com
    *Email Verified: YES
    
    1. Vaya a "Credentials" y Settee o Resetee la contraseña
        *Contraseña: admin123
        *Temporary: OFF
        SAVE

5. Ir a "Realm roles" y agreguen el rol "admin" 
    *Role Name: admin

6. En "Users", "Role mapping" selecciones "assing role" y marque "admin" y luego "assing"

7. Intentar iniciar sesion con el username y contraseña