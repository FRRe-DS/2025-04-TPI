from django.shortcuts import render
import logging
from time import perf_counter
from apps.apis.productoApi.client import ProductoAPIClient
import unicodedata

logger = logging.getLogger(__name__)

import unicodedata, re

def normalize(text):
    if not text:
        return ""
    # convertir todo a string siempre
    text = str(text)

    # eliminar caracteres invisibles
    text = (
        text.replace("\u00a0", " ")   # NO-BREAK SPACE
            .replace("\u200b", "")   # ZERO WIDTH SPACE
            .replace("\u200c", "")
            .replace("\u200d", "")
            .replace("\ufeff", "")
            .strip()
    )

    # bajar a minúsculas
    text = text.lower()

    # normalizar tildes
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")

    # colapsar múltiples espacios
    text = re.sub(r"\s+", " ", text)

    return text


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
        limit = int(request.GET.get("limit", 18))
        if limit < 1:
            limit = 18
    except Exception:
        limit = 18

    productos = []
    pagination_context = {}
    start = perf_counter()
    try:
        client = ProductoAPIClient(base_url="http://localhost:8000")
        
        logger.debug("Llamando a StockClient.listar_productos con limit=5000 para obtener todos los resultados filtrados=%s", {
            "busqueda": termino_busqueda,
            "categoria": categoria_filtrada,
            "marca": marca_filtrada,
        })
        
        # Una sola llamada: traer muchos productos para aplicar filtros y paginar localmente
        resultado = client.listar_productos(
            page=1, 
            limit=5000,
            search=termino_busqueda,
        )
        

        elapsed = perf_counter() - start
        logger.info("Stock API listar_productos respondió en %.3fs", elapsed)
        if isinstance(resultado, dict) and "data" in resultado:
            productos_raw = resultado.get("data") or []
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
        logger.exception("Error obteniendo productos desde Stock API para path=%s user=%s: %s", request.get_full_path(), getattr(request, "user", None), e)
        productos = []

    # Extraer categorías y marcas disponibles ANTES de filtrar
    categorias_disponibles = sorted({p.get("categoria", "") for p in productos if p.get("categoria", "")})
    marcas_disponibles = sorted({p.get("marca", "") for p in productos if p.get("marca", "")})

    # =============================
    #     FILTROS CON NORMALIZE
    # =============================

    q = normalize(termino_busqueda)
    cat_f = normalize(categoria_filtrada)
    marca_f = normalize(marca_filtrada)

    def _filtrar(prod):
        nombre = normalize(prod.get("nombre", ""))        
        marca = normalize(prod.get("marca", ""))
        categoria = normalize(prod.get("categoria", ""))

        # búsqueda general
        if q and (q not in nombre and q not in marca):
            return False

        # categoría
        if cat_f and cat_f != categoria:
            return False

        # marca
        if marca_f and marca_f != marca:
            return False

        # precio
        try:
            precio = prod.get("precio", 0)
            if precio_minimo and float(precio_minimo) > precio:
                return False
            if precio_maximo and float(precio_maximo) < precio:
                return False
        except:
            pass

        return True

    productos = [p for p in productos if _filtrar(p)]

    # Paginación manual después de filtrar
    total_resultados = len(productos)
    per_page = limit  # 18 productos por página
    total_pages = max(1, (total_resultados + per_page - 1) // per_page) if total_resultados > 0 else 1
    
    # Validar página
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages
    
    # Calcular índices para slice
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    productos_pagina = productos[start_idx:end_idx]
    
    pagination_context = {
        "total": total_resultados,
        "per_page": per_page,
        "current_page": page,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
        "next_page": page + 1 if page < total_pages else None,
        "prev_page": page - 1 if page > 1 else None,
    }

    logger.debug(
        "Filtros aplicados: busqueda=%s categoria=%s marca=%s precio_min=%s precio_max=%s -> %d resultados (página %d de %d)",
        termino_busqueda, categoria_filtrada, marca_filtrada, precio_minimo, precio_maximo, total_resultados, page, total_pages
    )

    carrito = []
    total_carrito = 0.0

    context = {
        "productos": productos_pagina,
        "categorias": categorias_disponibles,
        "marcas": marcas_disponibles,
        "filtros": {
            "busqueda": termino_busqueda,
            "categoria": categoria_filtrada,
            "marca": marca_filtrada,
            "precio_minimo": precio_minimo,
            "precio_maximo": precio_maximo,
        },
        "cantidad_resultados": total_resultados,
        "carrito": carrito,
        "total_carrito": total_carrito,
        "pagination": pagination_context,
    }

    logger.info("Renderizando inicio.html con %d productos de %d totales (página %d de %d)", len(productos_pagina), total_resultados, page, total_pages)
    return render(request, "inicio.html", context)
