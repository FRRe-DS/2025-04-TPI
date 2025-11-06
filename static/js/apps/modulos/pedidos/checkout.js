document.addEventListener('DOMContentLoaded', () => {
        let currentStep = 1;
        const steps = document.querySelectorAll('.checkout-step');
        const stepIndicators = document.querySelectorAll('.stepper .step');
        const orderStatusCard = document.getElementById('order-status-card');
        
        const summaryItemsContainer = document.querySelector('.summary-items');
        const totalsSummaryContainer = document.querySelector('.totals-summary');

        const formatPrice = (value) => {
            return `$ ${Number(value).toLocaleString('es-AR')}`;
        };

        const renderSummaryItems = () => {
            const carrito = JSON.parse(sessionStorage.getItem('carrito_demo')) || [];
            if (!summaryItemsContainer) return;
            summaryItemsContainer.innerHTML = '';
            let subtotal = 0;
            if (carrito.length === 0) {
                summaryItemsContainer.innerHTML = '<p class="cart-empty-summary">No hay productos en el carrito.</p>';
            } else {
                carrito.forEach(item => {
                    const precio = parseFloat(String(item.precio).replace(',', '.')) || 0;
                    const cantidad = item.cantidad || 1;
                    const itemSubtotal = precio * cantidad;
                    subtotal += itemSubtotal;

                    const div = document.createElement('div');
                    div.className = 'summary-item';
                    div.innerHTML = `
                        <img src="${item.imagen || 'https://via.placeholder.com/120x120/f1f1f1/cccccc?text=Producto'}" alt="${item.nombre}" class="item-image">
                        <div class="item-details">
                            <p>${item.nombre}</p>
                            <span>${item.talle ? 'Talle: ' + item.talle : ''}${item.talle ? ' ' : ''}${cantidad > 1 ? 'x' + cantidad : ''}</span>
                        </div>
                        <span class="item-price">${formatPrice(itemSubtotal)}</span>
                    `;
                    summaryItemsContainer.appendChild(div);
                });
            }

            // Calcular envío según opción seleccionada
            let envio = 0;
            const shippingRadio = document.querySelector('input[name="tipo_envio"]:checked');
            if (shippingRadio) {
                if (shippingRadio.value === 'domicilio') envio = 3500;
                else if (shippingRadio.value === 'retiro_sucursal') envio = 0;
                else if (shippingRadio.value === 'envio_expres') envio = 8500;
                else if (shippingRadio.value === 'demo_tracking') envio = 0;
            }

            if (totalsSummaryContainer) {
                const rows = totalsSummaryContainer.querySelectorAll('.total-row span:last-child');
                if (rows && rows.length >= 3) {
                    rows[0].textContent = formatPrice(subtotal);
                    rows[1].textContent = formatPrice(envio);
                    rows[2].textContent = formatPrice(subtotal + envio);
                }
            }
        };

        const populateFinalSummary = () => {
            // Obtener valores del formulario
            const nombre = document.getElementById('nombre').value;
            const telefono = document.getElementById('telefono').value;
            const calle = document.getElementById('calle').value;
            const depto = document.getElementById('departamento').value;
            const ciudad = document.getElementById('ciudad').value;
            const cp = document.getElementById('codigo_postal').value;
            
            // Obtener método de envío
            const shippingRadio = document.querySelector('input[name="tipo_envio"]:checked');
            const shippingSection = document.getElementById('summary-shipping-section');
            
            // Poblar datos de contacto
            document.getElementById('summary-nombre').textContent = nombre || 'No especificado';
            document.getElementById('summary-telefono').textContent = telefono || 'No especificado';

            if (shippingRadio) {
                if (shippingRadio.value === 'domicilio') {
                    shippingSection.style.display = 'block';

                    let addressLine1 = calle;
                    if (depto) {
                        addressLine1 += `, ${depto}`;
                    }

                    document.getElementById('summary-address-line1').textContent = addressLine1;
                    document.getElementById('summary-address-line2').textContent = `${ciudad}, ${cp}`;
                    document.getElementById('summary-shipping-method').textContent = "Envío a domicilio";

                    if (orderStatusCard) {
                        orderStatusCard.classList.add('hidden');
                    }
                } else if (shippingRadio.value === 'demo_tracking') {
                    shippingSection.style.display = 'none';
                    document.getElementById('summary-shipping-method').textContent = "Demo con seguimiento";

                    if (orderStatusCard) {
                        orderStatusCard.classList.remove('hidden');
                        orderStatusCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                } else {
                    shippingSection.style.display = 'none';
                    document.getElementById('summary-shipping-method').textContent = "Retiro en sucursal";

                    if (orderStatusCard) {
                        orderStatusCard.classList.add('hidden');
                    }
                }
            } else {
                shippingSection.style.display = 'none';
                document.getElementById('summary-shipping-method').textContent = "Sin definir";

                if (orderStatusCard) {
                    orderStatusCard.classList.add('hidden');
                }
            }
            // Asegurarnos de que el resumen lateral refleje el carrito actual y el envío elegido
            renderSummaryItems();
        };

        const updateStepUI = () => {
            steps.forEach(step => step.classList.add('hidden'));
            const activeStepContent = document.querySelector(`.checkout-step[data-step="${currentStep}"]`);
            if (activeStepContent) {
                activeStepContent.classList.remove('hidden');
            }

            // Si estamos en el último paso, poblamos el resumen
            if (currentStep === 3) {
                populateFinalSummary();
            }

            stepIndicators.forEach((indicator, index) => {
                const stepNumber = index + 1;
                indicator.classList.remove('active', 'completed');
                
                const nextConnector = indicator.nextElementSibling;
                let progressLine = null;
                if(nextConnector && nextConnector.classList.contains('step-connector')) {
                    progressLine = nextConnector.querySelector('.connector-line-progress');
                }

                if (stepNumber < currentStep) {
                    indicator.classList.add('completed');
                    if (progressLine) {
                        progressLine.style.width = '100%';
                        progressLine.style.backgroundColor = 'var(--color-green)';
                    }
                } else if (stepNumber === currentStep) {
                    indicator.classList.add('active');
                    if (progressLine) {
                       // La línea del paso activo comienza a llenarse
                       setTimeout(() => { 
                          progressLine.style.width = '50%';
                          progressLine.style.backgroundColor = 'var(--color-active)';
                       }, 50);
                    }
                } else {
                    // Pasos futuros
                    if (progressLine) {
                       progressLine.style.width = '0%';
                    }
                }
            });
        };

        document.querySelectorAll('.btn-next').forEach(button => {
            button.addEventListener('click', () => {
                if (currentStep < steps.length) {
                    currentStep++;
                    updateStepUI();
                }
            });
        });

        document.querySelectorAll('.btn-prev').forEach(button => {
            button.addEventListener('click', () => {
                if (currentStep > 1) {
                    currentStep--;
                    updateStepUI();
                }
            });
        });

        document.querySelectorAll('.btn-secondary').forEach(button => {
            button.addEventListener('click', () => {
                window.location.href = '/';
            });
        });
        
        const shippingDetailsSection = document.getElementById('shipping-details');
        const shippingRadios = document.querySelectorAll('input[name="tipo_envio"]');
        const toggleShippingDetails = () => {
            const selected = document.querySelector('input[name="tipo_envio"]:checked');
            if (selected && selected.value !== 'retiro_sucursal') {
                shippingDetailsSection.style.display = 'block';
            } else {
                shippingDetailsSection.style.display = 'none';
            }
            // cuando cambia el método de envío, recalculamos totales
            renderSummaryItems();
        };
        shippingRadios.forEach(radio => radio.addEventListener('change', toggleShippingDetails));
        
        updateStepUI();
        toggleShippingDetails();
        // Render inicial del resumen con los productos en sessionStorage
        renderSummaryItems();

        // Escuchar cambios de carrito (disparado desde base.html cuando el usuario modifica el carrito)
        document.addEventListener('cartUpdated', (e) => {
            renderSummaryItems();
        });
    });