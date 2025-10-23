from django.shortcuts import render
import logging
from time import perf_counter
from apps.apis.productoApi.client import ProductoAPIClient

logger = logging.getLogger(__name__)


def inicio_view(request):
    """Obtiene productos desde la API de Stock (sin datos hardcodeados)."""
    logger.info("inicio_view llamada: user=%s path=%s", getattr(request, "user", None), request.get_full_path())

    # parámetros de filtros y paginación
    termino_busqueda = request.GET.get("busqueda", "").strip()
    categoria_filtrada = request.GET.get("categoria", "").strip()
    marca_filtrada = request.GET.get("marca", "").strip()
    precio_minimo = request.GET.get("precio_minimo", "").strip()
    precio_maximo = request.GET.get("precio_maximo", "").strip()
    try:
        page = int(request.GET.get("page", 1))
        if page < 1:
            page = 1
    except Exception:
        page = 1
    try:
        limit = int(request.GET.get("limit", 20))
        if limit < 1:
            limit = 20
    except Exception:
        limit = 20

    productos = []
    pagination_context = {}
    start = perf_counter()
    try:
        client = ProductoAPIClient(base_url="http://localhost:8000")
        
        logger.debug("Llamando a StockClient.listar_productos page=%s limit=%s filtros=%s", page, limit, {
            "busqueda": termino_busqueda,
            "categoria": categoria_filtrada,
            "marca": marca_filtrada,
        })
        resultado = client.listar_productos(page=page, limit=limit)
        print('resultados',resultado,)

        elapsed = perf_counter() - start
        logger.info("Stock API listar_productos respondió en %.3fs", elapsed)
        if isinstance(resultado, dict) and "data" in resultado:
            productos_raw = resultado.get("data") or []
            pag = resultado.get("pagination") or resultado.get("meta") or {}
            total = pag.get("total") or pag.get("total_count") or pag.get("count")
            per_page = pag.get("per_page") or pag.get("limit") or limit
            current = pag.get("page") or page
            total_pages = None
            try:
                if total and per_page:
                    total_pages = max(1, (int(total) + int(per_page) - 1) // int(per_page))
            except Exception:
                logger.warning("No se pudo calcular total_pages para paginación: total=%s per_page=%s", total, per_page)
                total_pages = None
            pagination_context = {
                "total": total,
                "per_page": per_page,
                "current_page": current,
                "total_pages": total_pages,
                "has_next": (total_pages is not None and current < total_pages) or bool(pag.get("next")),
                "has_prev": (current and current > 1) or bool(pag.get("previous")),
                "next_page": (current + 1) if (total_pages is None or current < total_pages) else None,
                "prev_page": (current - 1) if (current and current > 1) else None,
            }
        else:
            if resultado is None:
                logger.warning("Stock API devolvió None en listar_productos")
            elif not isinstance(resultado, list):
                logger.warning("Formato inesperado de respuesta de Stock API: %s", type(resultado))
            productos_raw = resultado or []

        for p in productos_raw:
            categoria = None
            if isinstance(p.get("categoria"), dict):
                categoria = p["categoria"].get("nombre")
            else:
                categoria = p.get("categoria_nombre") or p.get("categoria")

            imagen = p.get("imagen_url") or p.get("imagen") or p.get("imagenUrl")

            precio = p.get("precio")
            try:
                precio = float(precio) if precio is not None else 0.0
            except Exception:
                logger.debug("Precio inválido para producto id=%s precio_raw=%s", p.get("id") or p.get("pk"), p.get("precio"))
                precio = 0.0

            productos.append({
                "id": p.get("id") or p.get("pk"),
                "nombre": p.get("nombre") or p.get("title") or "",
                "descripcion": p.get("descripcion") or p.get("description") or "",
                "precio": precio,
                "categoria": categoria or "",
                "marca": p.get("marca") or "",
                "imagen": imagen or "",
            })
        logger.info("Obtenidos %d productos (raw=%d) desde Stock API", len(productos), len(productos_raw))
    except Exception as e:
        # No fallback a datos hardcodeados: registramos y devolvemos lista vacía
        logger.exception("Error obteniendo productos desde Stock API para path=%s user=%s: %s", request.get_full_path(), getattr(request, "user", None), e)
        productos = []

    # aplicar filtros locales
    def _filtrar(prod):
        if termino_busqueda:
            if termino_busqueda.lower() not in prod.get("nombre", "").lower() and termino_busqueda.lower() not in prod.get("descripcion", "").lower():
                return False
        if categoria_filtrada and prod.get("categoria") != categoria_filtrada:
            return False
        if marca_filtrada and prod.get("marca") != marca_filtrada:
            return False
        try:
            if precio_minimo and float(precio_minimo) > prod.get("precio", 0):
                return False
            if precio_maximo and float(precio_maximo) < prod.get("precio", 0):
                return False
        except Exception:
            pass
        return True

    productos = [p for p in productos if _filtrar(p)]

    logger.debug("Filtros aplicados: busqueda=%s categoria=%s marca=%s precio_min=%s precio_max=%s -> %d resultados", termino_busqueda, categoria_filtrada, marca_filtrada, precio_minimo, precio_maximo, len(productos))

    categorias_disponibles = sorted({producto.get("categoria", "") for producto in productos})
    marcas_disponibles = sorted({producto.get("marca", "") for producto in productos})

    # carrito: por ahora no hay datos locales hardcodeados; usar vacío o cargar desde sesión/BD más adelante
    carrito = []
    total_carrito = 0.0

    context = {
        "productos": productos,
        "categorias": categorias_disponibles,
        "marcas": marcas_disponibles,
        "filtros": {
            "busqueda": termino_busqueda,
            "categoria": categoria_filtrada,
            "marca": marca_filtrada,
            "precio_minimo": precio_minimo,
            "precio_maximo": precio_maximo,
        },
        "cantidad_resultados": len(productos),
        "carrito": carrito,
        "total_carrito": total_carrito,
        "pagination": pagination_context,
    }
    logger.info("Renderizando inicio.html con %d productos (page=%s, limit=%s)", len(productos), page, limit)
    return render(request, "inicio.html", context)

