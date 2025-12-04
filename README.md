# 📱 Portal de Compras - Grupo 04 (Compras)

> **Informe Técnico del Proyecto Integrador - Desarrollo de Software 2025**

## ⚡ Inicio Rápido (Docker)

```bash
# Clonar el repositorio
git clone https://github.com/frre-ds/2025-grupo-04-compras.git
cd 2025-04-TPI

# Levantar todos los servicios con Docker
docker-compose up --build

# ✅ Una vez que veas "Application startup complete", abre en tu navegador:
# http://localhost
```

---

## 📑 Tabla de Contenidos

1. [Inicio Rápido (Docker)](#inicio-rápido-docker) ← **COMIENZA AQUÍ**
2. [Descripción General](#descripción-general)
3. [Arquitectura del Sistema](#arquitectura-del-sistema)
4. [Características Principales](#características-principales)
5. [Tecnologías Utilizadas](#tecnologías-utilizadas)
6. [Instalación y Setup](#instalación-y-setup)
7. [Ejecución del Proyecto](#ejecución-del-proyecto)
8. [Estructura del Proyecto](#estructura-del-proyecto)
9. [Autenticación y Seguridad](#autenticación-y-seguridad)
10. [APIs Integradas](#apis-integradas)
11. [Panel de Administración](#panel-de-administración)
12. [Pruebas](#pruebas)
13. [Despliegue con Docker](#despliegue-con-docker)
14. [Documentación Adicional](#documentación-adicional)

---

## 📖 Descripción General

El **Portal de Compras (Grupo 04)** es un módulo backend especializado en la gestión integral de compras, carritos de compras y pedidos. Forma parte de una arquitectura distribuida de microservicios coordinada con otros grupos de desarrollo:

- **Grupo 02 (Stock):** Gestión de inventario y productos
- **Grupo 03 (Logística):** Gestión de envíos y entregas
- **Grupo 04 (Compras - Este Proyecto):** Procesamiento de pedidos y carrito de compras

El sistema está desarrollado con **Django 5.1** e integra autenticación centralizada mediante **Keycloak**, permitiendo una experiencia de usuario unificada en la plataforma.

---

## 🏗️ Arquitectura del Sistema

```
┌──────────────────────────────────────────────────────────────┐
│                     NGINX (Proxy Reverso)                    │
│                    Puerto 80 - Balanceador                   │
└─────────┬────────────────────┬────────────────────┬───────────┘
          │                    │                    │
    ┌─────▼──────┐      ┌──────▼──────┐      ┌─────▼──────┐
    │   Django   │      │  G02 Stock  │      │ G03 Logís  │
    │  (Compras) │      │   Backend   │      │  Backend   │
    │ :8000      │      │   :4000     │      │  :3010     │
    └─────┬──────┘      └──────┬──────┘      └─────┬──────┘
          │                    │                    │
    ┌─────▼──────┐      ┌──────▼──────┐      ┌─────▼──────┐
    │ PostgreSQL │      │  Supabase   │      │   MySQL    │
    │            │      │  (G02)      │      │ (Logística)│
    └────────────┘      └─────────────┘      └────────────┘

        ┌──────────────────────────────────────────┐
        │   KEYCLOAK (Autenticación Centralizada)  │
        │            :8080                        │
        └──────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│     FRONTEND STOCK (Next.js - G02)  :3000                    │
│     FRONTEND ADMIN (React/HTML - G04)                        │
└──────────────────────────────────────────────────────────────┘
```

---

## ✨ Características Principales

### 🛒 Gestión de Carrito
- Crear y modificar carritos de compras
- Agregar/remover productos del carrito
- Calcular totales y aplicar impuestos
- Persistencia en base de datos

### 📦 Gestión de Pedidos
- Crear pedidos desde el carrito
- Seguimiento de estado de pedidos (Borrador → Pendiente → Confirmado → Cancelado)
- Reserva automática de stock
- Notificaciones por email en cada cambio de estado
- Referencias de reserva y envío

### 👥 Administración de Usuarios
- Autenticación integrada con Keycloak
- Roles y permisos centralizados
- Perfil de usuario personalizado
- Soporte para múltiples métodos de login

### 🔐 Seguridad
- Autenticación OAuth2/OpenID Connect
- Middleware para validación de tokens JWT
- Protección CSRF
- Validación de entrada y sanitización

### 📊 Panel Administrativo
- Dashboard con KPIs en tiempo real
- Gestión de pedidos y carritos
- Monitoreo de transacciones
- Redirección centralizada a módulos de otros grupos

### 🔗 Integración de APIs
- **Stock API (G02):** Consulta y reserva de productos
- **Logística API (G03):** Gestión de envíos
- **APIs Mock:** Para desarrollo y pruebas

---

## 💻 Tecnologías Utilizadas

### Backend
| Tecnología | Versión | Propósito |
|-----------|---------|----------|
| **Django** | 5.1.1 | Framework web principal |
| **Django REST Framework** | 3.14.0 | Construcción de APIs REST |
| **PostgreSQL** | 16.2 | Base de datos principal |
| **Gunicorn** | 23.0.0 | Servidor WSGI para producción |
| **Python** | 3.10+ | Lenguaje de programación |

### Autenticación y Autorización
| Tecnología | Propósito |
|-----------|----------|
| **Keycloak** | 23.0.6 - Servidor de autenticación centralizado |
| **django-allauth** | Autenticación social (Google, GitHub, etc.) |
| **djangorestframework-simplejwt** | Manejo de tokens JWT |
| **python-keycloak** | Integración con Keycloak |

### Frontend
| Tecnología | Propósito |
|-----------|----------|
| **Django Templates** | Renderizado de vistas HTML |
| **HTML5/CSS3/JavaScript** | Interfaz de usuario |
| **Bootstrap** | Framework CSS responsivo |
| **Boxicons** | Iconografía |

### DevOps y Despliegue
| Tecnología | Propósito |
|-----------|----------|
| **Docker** | Containerización |
| **Docker Compose** | Orquestación de servicios |
| **Nginx** | Proxy reverso y balanceador |
| **Git** | Control de versiones |

### Herramientas de Desarrollo
| Herramienta | Propósito |
|-----------|----------|
| **Pytest** | Testing unitario |
| **Black** | Formateador de código |
| **Flake8** | Linter Python |
| **DjangoShell** | Consola interactiva |

---

## 📥 Instalación y Setup

### Requisitos Previos

```bash
- Python 3.10 o superior
- Git
- Docker y Docker Compose (para despliegue)
- PostgreSQL 16+ (si no usas Docker)
```

### Opción 1: Instalación Rápida (Express)

```bash
git clone https://github.com/FRRe-DS/2025-04-TPI.git
cd 2025-04-TPI

# Crear y activar entorno virtual
python -m venv venv
.\venv\Scripts\Activate.ps1    # Windows
# source venv/bin/activate    # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar migraciones
python manage.py migrate

# Verificar instalación
python verificar_instalacion.py

# Crear superusuario
python manage.py createsuperuser
```

### Opción 2: Instalación Detallada

Lee **[INSTALACION.md](INSTALACION.md)** para instrucciones paso a paso completas.

### Opción 3: Instalación con Docker (Recomendado)

```bash
# Construir y levantar todos los servicios
docker-compose up --build

# O usar el script batch (Windows)
.\rebuild_stack.bat
```

---

## 🚀 Ejecución del Proyecto

### ⭐ Opción Recomendada: Docker (Producción/Desarrollo)

```bash
# Levantar todos los servicios
docker-compose up --build

# O en background
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f django

# Detener servicios
docker-compose down
```

**Acceso:** http://localhost:8000

### Acceso a la Aplicación

| Componente | URL | Descripción |
|-----------|-----|-----------|
| **Frontend** | http://localhost:8000 | Aplicación web principal |
| **Admin Panel** | http://localhost:8000/administracion | Panel administrativo |
| **API REST** | http://localhost:8000/api/ | APIs REST |
| **Swagger/OpenAPI** | http://localhost:8000/api/docs/ | Documentación interactiva |
| **Django Admin** | http://localhost:8000/admin | Panel admin de Django |
| **Keycloak** | http://localhost:8080 | Servidor de autenticación |
| **Stock Frontend (G02)** | http://localhost:3000 | Frontend de inventario |

### Scripts Disponibles (Windows)

```bash
run.bat                    # Ejecutar servidor (desarrollo local)
makemigrations.bat         # Crear migraciones
migrate.bat               # Aplicar migraciones
up-image.bat             # Construir imagen Docker
rebuild_stack.bat        # Reconstruir stack completo (RECOMENDADO)
```

---

## 📂 Estructura del Proyecto

```
2025-04-TPI/
├── apps/                          # Aplicaciones Django
│   ├── apis/                      # APIs de terceros
│   │   ├── carritoApi/           # API de Carrito
│   │   ├── pedidoApi/            # API de Pedidos
│   │   └── productoApi/          # API de Productos
│   └── modulos/                   # Módulos de negocio
│       ├── administracion/       # Panel administrativo
│       ├── inicio/               # Página de inicio
│       ├── login/                # Autenticación
│       └── pedidos/              # Gestión de pedidos
│
├── Main/                          # Configuración principal
│   ├── settings.py               # Configuración de Django
│   ├── urls.py                   # Rutas principales
│   ├── wsgi.py                   # WSGI para producción
│   ├── asgi.py                   # ASGI para desarrollo
│   ├── middleware_request_id.py  # Middleware personalizado
│   ├── backends.py               # Backends de autenticación
│   └── logging_filters.py        # Configuración de logs
│
├── templates/                     # Plantillas HTML
│   ├── base.html                 # Template base
│   ├── baseAdmin.html            # Template admin
│   ├── admin_menu_principal.html # Menú administrativo
│   ├── componentesBase/          # Componentes reutilizables
│   └── emails/                   # Templates de emails
│
├── static/                        # Archivos estáticos
│   ├── css/                      # Hojas de estilos
│   ├── js/                       # JavaScript
│   ├── imagenes/                 # Imágenes y assets
│   └── lottie/                   # Animaciones Lottie
│
├── utils/                         # Utilidades
│   ├── apiCliente/               # Clientes HTTP para APIs
│   ├── keycloak.py               # Integración Keycloak
│   └── color_log_formatter.py    # Formateador de logs
│
├── tests/                         # Suite de pruebas
│   ├── test_apis_mock_completo.py
│   ├── test_checkout_flow.py
│   └── mocks/                    # Datos y mocks para testing
│
├── documentacion/                 # Documentación
│   ├── APIS_MOCK_COMPLETADO.md
│   ├── IMPLEMENTACION_COMPLETADA.md
│   ├── PETICIONES_COMPRAS_A_LOGISTICA_STOCK.md
│   ├── openAPI/                  # Especificaciones OpenAPI
│   └── Responsabilidades/        # Distribución de tareas
│
├── keycloak/                      # Configuración Keycloak
│   ├── docker-compose.yml
│   ├── realm-config/
│   └── README.md
│
├── nginx/                         # Configuración Nginx
│   ├── nginx.conf
│   └── nginxcategra.config
│
├── docker-compose.yml             # Orquestación de servicios
├── Dockerfile                     # Imagen Docker
├── requirements.txt               # Dependencias Python
├── manage.py                      # CLI de Django
├── INSTALACION.md                 # Guía de instalación
├── INICIO_RAPIDO.md               # Inicio rápido
└── README.md                      # Este archivo
```

---

## 🔐 Autenticación y Seguridad

### Flujo de Autenticación

```
Usuario
  ↓
[Login/Registro] → Keycloak
  ↓
[Token JWT] → Django (Validación)
  ↓
[Sesión iniciada] → Acceso a recursos protegidos
```

### Configuración Keycloak

**Realm:** `ds-2025-realm`

**Cliente:** `grupo-04`

**Credenciales:** Configuradas en `.env`

```python
KEYCLOAK_BASE_URL = http://keycloak:8080
KEYCLOAK_REALM = ds-2025-realm
KEYCLOAK_CLIENT_ID = grupo-04
KEYCLOAK_CLIENT_SECRET = [SECRET]
```

### Middleware de Seguridad

- **Request ID Middleware:** Genera ID único para cada solicitud
- **CORS Middleware:** Validación de origen
- **Token Validation:** Validación de JWT en headers
- **CSRF Protection:** Protección contra ataques CSRF

---

## 🔗 APIs Integradas

### 1. Stock API (Grupo 02)

**Base URL:** `http://nginx/stock/`

**Métodos Disponibles:**

```python
# Cliente: StockClient
client = StockClient()

# Obtener producto por ID
producto = client.obtener_producto(producto_id=1)

# Reservar stock
reserva = client.reservar_stock(
    idCompra="PEDIDO-001",
    usuarioId=5,
    productos=[
        {"idProducto": 1, "cantidad": 2},
        {"idProducto": 3, "cantidad": 1}
    ]
)

# Liberar stock
liberar = client.liberar_stock(
    idReserva=42,
    usuarioId=5,
    motivo="Pedido cancelado"
)
```

### 2. Logística API (Grupo 03)

**Base URL:** `http://shipping-back:3010`

**Métodos Disponibles:**

```python
# Cliente: LogisticsClient
client = LogisticsClient()

# Crear envío
envio = client.crear_envio(
    pedido_id="PEDIDO-001",
    direccion="Calle Principal 123",
    ciudad="Córdoba"
)

# Rastrear envío
estado = client.obtener_estado_envio(envio_id=42)
```

### 3. APIs Mock (Desarrollo)

Para desarrollo sin dependencias externas:

```python
# En settings.py
USE_MOCK_APIS = True

# Las APIs retornarán datos de prueba
```

---

## 👨‍💼 Panel de Administración

### Acceso

**URL:** `http://localhost:8000/administracion`

### Funcionalidades

#### 1. Dashboard Principal
- KPIs en tiempo real (ingresos, pedidos, usuarios)
- Últimas transacciones
- Gráficos de rendimiento

#### 2. Gestión de Pedidos
- Listado de todos los pedidos
- Filtrar por estado, usuario, fecha
- Ver detalles completos del pedido
- Cambiar estado del pedido
- Descargar factura/comprobante

#### 3. Gestión de Carritos
- Ver carritos activos de usuarios
- Análisis de abandono de carrito
- Estadísticas de compra

#### 4. Menú de Módulos
- **Stock:** Redirecciona a `http://localhost:3000` (Frontend Stock G02)
- **Logística:** Redirecciona a módulo de Logística (G03)
- **Compras:** Dashboard actual

### Panel Admin Actualizado

**Cambio Reciente:** El botón "Stock" del panel de administración ahora redirecciona correctamente al frontend del Grupo 02 (Stock) en `http://localhost:3000`.

```html
<!-- Antes -->
<a href="{% url 'admin_stock' %}">Stock</a>

<!-- Ahora -->
<a href="http://localhost:3000" target="_blank">Stock</a>
```

---

## 🧪 Pruebas

### Ejecutar Suite de Pruebas Completa

```bash
# Todas las pruebas
python -m pytest tests/

# O usar script de verificación
python verificar_instalacion.py

# Pruebas específicas
python -m pytest tests/test_apis_mock_completo.py -v
python -m pytest tests/test_checkout_flow.py -v
```

### Pruebas Disponibles

| Prueba | Descripción |
|--------|-----------|
| `test_apis_mock_completo.py` | Validación completa de APIs mock |
| `test_checkout_flow.py` | Flujo completo de checkout |
| `test_logistics_client.py` | Integración con Logística |
| `test_integracion_apis.py` | Integración entre servicios |

### Coverage

```bash
# Generar reporte de cobertura
python -m pytest --cov=apps tests/
```

---

## 🐳 Despliegue con Docker

### Inicio Rápido (Recomendado)

```bash
# Opción 1: Reconstruir desde cero
docker-compose down -v
docker-compose up --build

# Opción 2: Si ya tienes los servicios, simplemente:
docker-compose up

# Opción 3: En background
docker-compose up -d
```

### Esperar a que el servidor esté listo

Busca este mensaje en los logs:

```
django_1 | INFO:     Application startup complete
```

Una vez que veas eso, accede a: **http://localhost:8000**

### Construcción de Imagen

```bash
# Construir imagen local
docker build -t grupo-04-compras:latest .

# O usar script
up-image.bat
```

### Monitoreo de Servicios

```bash
# Listar contenedores en ejecución
docker ps

# Ver logs de todos los servicios
docker-compose logs

# Ver logs solo del Django
docker-compose logs -f django

# Ver logs de Keycloak
docker-compose logs -f keycloak

# Detener servicios
docker-compose down

# Detener y eliminar volúmenes (CUIDADO: borra datos)
docker-compose down -v
```

### Estructura Docker Compose

| Servicio | Puerto | Estado | Propósito |
|---------|--------|--------|----------|
| **django** | 8000 | Backend principal | Aplicación web |
| **postgres** | 5432 (interno) | Base de datos | PostgreSQL |
| **nginx** | 80 | Proxy reverso | Balanceador |
| **keycloak** | 8080 | Autenticación | OAuth2/OpenID |
| **stock-backend** | 4000 | Backend Stock (G02) | API Stock |
| **stock_frontend** | 3000 | Frontend Stock (G02) | Inventario |
| **shipping-back** | 3010 | Backend Logística (G03) | API Logística |
| **mysql** | 3306 (interno) | BD Logística | MySQL |

---

## 📚 Documentación Adicional

### Documentos Principales

- **[INSTALACION.md](INSTALACION.md)** - Guía completa de instalación
- **[INICIO_RAPIDO.md](INICIO_RAPIDO.md)** - Inicio en 5 minutos
- **[MIGRACIONES_Y_DATOS.md](MIGRACIONES_Y_DATOS.md)** - Gestión de BD
- **[IMPLEMENTACION_COMPLETADA.md](documentacion/IMPLEMENTACION_COMPLETADA.md)** - Features implementadas

### Documentación de APIs

- **[OpenAPI Portal](documentacion/openAPI/)** - Especificaciones OpenAPI
- **[APIs Mock](documentacion/APIS_MOCK_COMPLETADO.md)** - Endpoints mock
- **[Peticiones a APIs](documentacion/PETICIONES_COMPRAS_A_LOGISTICA_STOCK.md)** - Ejemplos de solicitudes

### Responsabilidades por Módulo

- **[Administración](documentacion/Responsabilidades/ModuloAdministracion.md)**
- **[Pedidos](documentacion/Responsabilidades/MóduloPedidos.md)**
- **[Carrito API](documentacion/Responsabilidades/CarritoApi.md)**
- **[Inicio](documentacion/Responsabilidades/ModuloInicio.md)**
- **[Login](documentacion/Responsabilidades/ModuloLogin.md)**

---

## 🔧 Troubleshooting

### Problemas Comunes

#### Error: "ModuleNotFoundError: No module named 'django'"
```bash
# Solución: Activar entorno virtual e instalar dependencias
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

#### Error de Base de Datos
```bash
# Solución: Aplicar migraciones
python manage.py migrate
python manage.py migrate --run-syncdb
```

#### Puerto 8000 ya está en uso
```bash
# Solución: Ejecutar en puerto diferente
python manage.py runserver 8001
```

#### Error de Keycloak
```bash
# Verificar que Keycloak está corriendo
docker ps | grep keycloak

# Reiniciar Keycloak
docker-compose restart keycloak
```

---

## 📊 Estadísticas del Proyecto

| Métrica | Valor |
|---------|-------|
| **Líneas de Código Python** | ~3,500+ |
| **Líneas de HTML/Templates** | ~2,000+ |
| **Archivos de Configuración** | 20+ |
| **Endpoints API** | 15+ |
| **Modelos de BD** | 8+ |
| **Pruebas Unitarias** | 30+ |

---

## 👥 Equipo Responsable

**Grupo 04 - Módulo de Compras**

- **Desarrollo Backend:** Django, APIs, BD
- **Desarrollo Frontend:** Templates HTML, CSS, JavaScript
- **DevOps/Infraestructura:** Docker, Nginx, Keycloak
- **Testing:** Pruebas unitarias e integración

---

## 📝 Convenciones de Código

### Naming Conventions

```python
# Variables
usuario_id = 1
producto_nombre = "Laptop"

# Funciones
def obtener_pedido(pedido_id):
    pass

# Clases
class CarritoCompras:
    pass

# Constantes
LIMITE_ITEMS_CARRITO = 100
```

### Estructura de Respuestas API

```json
{
  "success": true,
  "status_code": 200,
  "data": {
    "id": 1,
    "nombre": "Producto"
  },
  "message": "Operación exitosa",
  "timestamp": "2025-04-12T10:30:00Z"
}
```

---

## 🔄 Flujos Principales

### Flujo de Compra

```
1. Usuario explora catálogo (Stock G02)
   ↓
2. Agrega productos al carrito
   ↓
3. Accede al checkout (Grupo 04)
   ↓
4. Sistema reserva stock (API Stock)
   ↓
5. Confirma compra y genera pedido
   ↓
6. Sistema notifica a Logística (API Logística)
   ↓
7. Envío se gestiona en G03
   ↓
8. Notificación al usuario
```

---

## 📞 Contacto y Soporte

Para consultas técnicas referidas a este módulo (Grupo 04 - Compras):

- Revisar documentación en `/documentacion/`
- Consultar responsabilidades por módulo
- Ejecutar `python verificar_instalacion.py` para diagnosticar
- Comunicarse con el Jefe del proyecto MAXIMO VAZQUEZ
---

## 📄 Licencia

Este proyecto forma parte del Proyecto Integrador 2025 de la Facultad Tecnológica Nacional (FRRe - Facultad Regional Resistencia).
   - Integrantes:
      - ACOSTA, Santiago
      - AGUIRRE, Joaquin
      - CETTOUR, Ivo
      - DUARTE, Hugo
      - MIRANDA, Ulises
      - PETRACCARO, Maximiliano
      - VAZQUEZ, Maximo
      - SVEDA, Juan Pablo
      - ZARACHO, Emanuel
      - ZARATE, Francisco
---

**Última actualización:** Diciembre 04, 2025
