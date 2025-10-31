document.addEventListener('DOMContentLoaded', () => {
    
    // --- LÓGICA PARA EL PANEL DE FILTROS RESPONSIVO ---
    const openFiltersBtn = document.getElementById('open-filters-btn');
    const closeFiltersBtn = document.getElementById('close-filters-btn');
    const filtersSidebar = document.getElementById('filters-sidebar');
    const filtersOverlay = document.getElementById('filters-overlay');

    function openFilters() {
        if (filtersSidebar) filtersSidebar.classList.add('open');
        if (filtersOverlay) filtersOverlay.classList.add('visible');
    }

    function closeFilters() {
        if (filtersSidebar) filtersSidebar.classList.remove('open');
        if (filtersOverlay) filtersOverlay.classList.remove('visible');
    }

    if (openFiltersBtn) openFiltersBtn.addEventListener('click', openFilters);
    if (closeFiltersBtn) closeFiltersBtn.addEventListener('click', closeFilters);
    if (filtersOverlay) filtersOverlay.addEventListener('click', closeFilters);
    
    // --- LÓGICA PARA LAS TARJETAS DE PRODUCTO ---
    const productCards = document.querySelectorAll('.product-card');
    let productoActivo = null;

    function confirmarProductoActivo() {
        if (productoActivo === null) return;
        const cardActiva = document.querySelector(`.product-card[data-id="${productoActivo}"]`);
        if (cardActiva) {
            const quantityInput = cardActiva.querySelector('.quantity-input');
            const cantidad = parseInt(quantityInput.value) || 0;
            const idConfirmado = productoActivo;
            
            // Limpiamos el estado ANTES de actualizar, para que la tarjeta se pueda redibujar.
            productoActivo = null;
            
            // Actualizamos el carrito. Esto disparará 'cartUpdated' para todas las tarjetas.
            window.actualizarCantidadProducto(idConfirmado, cantidad);
        } else {
            productoActivo = null;
        }
    }

    const actualizarVistaTarjeta = (card, carrito) => {
        const productId = card.dataset.id;
        const actionsContainer = card.querySelector('.card-actions');
        const addToCartBtn = actionsContainer.querySelector('.add-to-cart-btn');
        const quantitySelector = actionsContainer.querySelector('.quantity-selector');
        const confirmBtn = actionsContainer.querySelector('.confirm-btn');
        const quantityInput = actionsContainer.querySelector('.quantity-input');
        
        // Si la tarjeta está en modo edición, no la actualizamos desde aquí.
        if (productId === productoActivo) return;

        const productoEnCarrito = carrito.find(item => item.id === productId);
        if (productoEnCarrito) {
            // Estado normal: en el carrito (solo se ve el selector)
            addToCartBtn.classList.add('hidden');
            confirmBtn.classList.add('hidden');
            quantitySelector.classList.remove('hidden');
            quantityInput.value = productoEnCarrito.cantidad;
        } else {
            // Estado normal: no en el carrito (solo se ve "Agregar")
            addToCartBtn.classList.remove('hidden');
            confirmBtn.classList.add('hidden');
            quantitySelector.classList.add('hidden');
            quantityInput.value = 1;
        }
    };

    productCards.forEach(card => {
        const productId = card.dataset.id;
        const actionsContainer = card.querySelector('.card-actions');
        const addToCartBtn = actionsContainer.querySelector('.add-to-cart-btn');
        const confirmBtn = actionsContainer.querySelector('.confirm-btn');
        const plusBtn = actionsContainer.querySelector('.plus-btn');
        const minusBtn = actionsContainer.querySelector('.minus-btn');
        const quantityInput = actionsContainer.querySelector('.quantity-input');
        const quantitySelector = actionsContainer.querySelector('.quantity-selector');

        function entrarModoEdicion() {
            if (productoActivo !== null && productoActivo !== productId) {
                confirmarProductoActivo();
            }
            productoActivo = productId;
            
            // Vista de "modo edición"
            addToCartBtn.classList.add('hidden');
            quantitySelector.classList.remove('hidden');
            confirmBtn.classList.remove('hidden');
        }

        addToCartBtn.addEventListener('click', entrarModoEdicion);
        quantitySelector.addEventListener('click', (e) => {
            if (e.target.classList.contains('quantity-btn')) entrarModoEdicion();
        });

        quantityInput.addEventListener('input', () => {
            // 1. Filtra el valor para permitir solo números
            quantityInput.value = quantityInput.value.replace(/[^0-9]/g, '');
            // 2. Activa el modo edición para mostrar "Confirmar"
            entrarModoEdicion();
        });

        plusBtn.addEventListener('click', () => {
            quantityInput.value = (parseInt(quantityInput.value) || 0) + 1;
        });

        minusBtn.addEventListener('click', () => {
            const currentValue = parseInt(quantityInput.value);
            if (currentValue > 1) {
                quantityInput.value = currentValue - 1;
            }
        });
        
        confirmBtn.addEventListener('click', confirmarProductoActivo);
    });

    document.addEventListener('cartUpdated', (e) => {
        const carritoActual = e.detail.carrito;
        productCards.forEach(card => {
            actualizarVistaTarjeta(card, carritoActual);
        });
    });

    const carritoInicial = JSON.parse(sessionStorage.getItem('carrito_demo')) || [];
    productCards.forEach(card => {
        actualizarVistaTarjeta(card, carritoInicial);
    });
});