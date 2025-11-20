document.addEventListener('DOMContentLoaded', () => {
        let currentStep = 1;
        const steps = document.querySelectorAll('.checkout-step');
        const stepIndicators = document.querySelectorAll('.stepper .step');
        const orderStatusCard = document.getElementById('order-status-card');
        
        const summaryItemsContainer = document.querySelector('.summary-items');
        const totalsSummaryContainer = document.querySelector('.totals-summary');

        // Función para obtener CSRF token
        const getCSRFToken = () => {
            const match = document.cookie.match(new RegExp('(^| )csrftoken=([^;]+)'));
            if (match) return decodeURIComponent(match[2]);
            return null;
        };

        // Función para finalizar pedido - NUEVA
        const finalizarPedido = async (event) => {
            event.preventDefault();

            // Leer carrito mock desde sessionStorage
            const carrito = JSON.parse(sessionStorage.getItem("carrito_demo")) || [];

            if (carrito.length === 0) {
                alert("El carrito mock está vacío.");
                return;
            }

            const nombre = document.getElementById('nombre')?.value || '';
            const telefono = document.getElementById('telefono')?.value || '';
            const calle = document.getElementById('calle')?.value || '';
            const departamento = document.getElementById('departamento')?.value || '';
            const ciudad = document.getElementById('ciudad')?.value || '';
            const codigo_postal = document.getElementById('codigo_postal')?.value || '';
            const tipo_envio_el = document.querySelector('input[name="tipo_envio"]:checked');
            const tipo_transporte = tipo_envio_el?.value || "domicilio";

            // Validación: Nombre y teléfono siempre requeridos
            if (!nombre || !telefono) {
                alert("Por favor completa nombre y teléfono.");
                return;
            }

            // Validación condicional: Si NO es retiro en sucursal, requiere dirección
            if (tipo_transporte !== 'retiro_sucursal' && tipo_transporte !== 'demo_tracking') {
                if (!calle || !ciudad || !codigo_postal) {
                    alert("Por favor completa todos los campos de dirección.");
                    return;
                }
            }

            // Calcular costo de envío según tipo de transporte
            let costo_envio = 0;
            if (tipo_transporte === 'domicilio') costo_envio = 3500;
            else if (tipo_transporte === 'retiro_sucursal') costo_envio = 0;
            else if (tipo_transporte === 'envio_expres') costo_envio = 8500;
            else if (tipo_transporte === 'demo_tracking') costo_envio = 0;

            try {
                const resp = await fetch("/api/shopcart/checkout", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCSRFToken(),
                    },
                    body: JSON.stringify({
                        nombre_receptor: nombre,
                        telefono: telefono,
                        calle: calle,
                        departamento: departamento,
                        ciudad: ciudad,
                        cp: codigo_postal,
                        tipo_transporte: tipo_transporte,
                        costo_envio: costo_envio,   // 🔥 Incluir costo de envío
                        items: carrito   // 🔥 enviar carrito mock al backend
                    })
                });

                if (!resp.ok) {
                    const errorText = await resp.text();
                    console.error("Error al crear el pedido:", errorText);
                    alert("Error al crear el pedido.");
                    return;
                }

                const pedidoData = await resp.json();
                console.log("Pedido creado exitosamente:", pedidoData);
                
                // 🔥 Limpiar carrito mock del sessionStorage
                sessionStorage.setItem("carrito_demo", JSON.stringify([]));
                
                // Redirigir a mis pedidos
                window.location.href = "/pedidos/";
            } catch (error) {
                console.error("Error de red:", error);
                alert("Error de conexión al crear el pedido.");
            }
        };

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

        // Helpers para enviar el checkout al endpoint backend
        const getCookie = (name) => {
            const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
            if (match) return decodeURIComponent(match[2]);
            return null;
        };

        const buildPayload = () => {
            const carrito = JSON.parse(sessionStorage.getItem('carrito_demo')) || [];
            const products = carrito.map(item => {
                const pid = item.id || item.productId || item.producto_id || null;
                const qty = item.cantidad || item.quantity || item.qty || 1;
                return { productId: Number(pid), quantity: Number(qty) };
            }).filter(p => p.productId !== null);

            const address = {
                nombre_receptor: document.getElementById('nombre') ? document.getElementById('nombre').value : '',
                telefono: document.getElementById('telefono') ? document.getElementById('telefono').value : '',
                calle: document.getElementById('calle') ? document.getElementById('calle').value : '',
                departamento: document.getElementById('departamento') ? document.getElementById('departamento').value : '',
                ciudad: document.getElementById('ciudad') ? document.getElementById('ciudad').value : '',
                codigo_postal: document.getElementById('codigo_postal') ? document.getElementById('codigo_postal').value : '',
                provincia: document.getElementById('provincia') ? document.getElementById('provincia').value : '',
                pais: document.getElementById('pais') ? document.getElementById('pais').value : 'Argentina',
                informacion_adicional: document.getElementById('informacion_adicional') ? document.getElementById('informacion_adicional').value : '',
            };

            const transportRadio = document.querySelector('input[name="tipo_envio"]:checked');
            const transport_type = transportRadio ? transportRadio.value : '';

            const paymentElem = document.getElementById('payment_method');
            const payment_method = paymentElem ? paymentElem.value : 'card';

            const idCompra = 'client-' + Date.now();

            return {
                deliveryAddress: address,
                products: products,
                transport_type: transport_type,
                payment_method: payment_method,
                idCompra: idCompra
            };
        };

        const showOrderResult = (data, status) => {
            if (!orderStatusCard) return;
            orderStatusCard.classList.remove('hidden');
            orderStatusCard.innerHTML = '';
            if (status >= 200 && status < 300) {
                const pedido = data.pedido || {};
                const reserva = data.reserva || {};
                const envio = data.envio || {};
                orderStatusCard.innerHTML = `
                    <h3>Pedido confirmado</h3>
                    <p><strong>Pedido ID:</strong> ${pedido.id || '-'} - <strong>Estado:</strong> ${pedido.estado || '-'}</p>
                    <p><strong>Total:</strong> ${pedido.total || '-'}</p>
                    <p><strong>Reserva stock:</strong> ${reserva.id || reserva.reservationId || JSON.stringify(reserva)}</p>
                    <p><strong>Envío / Tracking:</strong> ${envio.id || envio.trackingId || JSON.stringify(envio)}</p>
                `;
            } else {
                orderStatusCard.innerHTML = `
                    <h3>Error procesando pedido</h3>
                    <p>${data && data.error ? data.error : 'Ocurrió un error al procesar el pedido.'}</p>
                    <pre style="white-space:pre-wrap">${data && data.detail ? JSON.stringify(data.detail) : ''}</pre>
                `;
            }
            orderStatusCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
        };

        const sendCheckout = async (e) => {
            e && e.preventDefault();
            const btn = e ? (e.currentTarget || e.target) : null;
            if (btn) btn.disabled = true;
            const payload = buildPayload();
            if (!payload.products || payload.products.length === 0) {
                alert('El carrito está vacío.');
                if (btn) btn.disabled = false;
                return;
            }

            try {
                const csrf = getCookie('csrftoken');
                const resp = await fetch('/pedidos/api/checkout/confirm/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrf || ''
                    },
                    body: JSON.stringify(payload)
                });
                const data = await resp.json().catch(() => ({}));
                showOrderResult(data, resp.status);
            } catch (err) {
                showOrderResult({ error: 'Error de red', detail: String(err) }, 500);
            } finally {
                if (btn) btn.disabled = false;
            }
        };

        // Conectar al botón de confirmación (id `confirm-order` o clase `.btn-confirm`) y al submit del formulario
        const confirmBtn = document.getElementById('confirm-order') || document.querySelector('.btn-confirm');
        if (confirmBtn) {
            confirmBtn.addEventListener('click', finalizarPedido);
        }

        // Si el botón final es un `submit` dentro del formulario, capturamos el submit
        const checkoutForm = document.querySelector('.checkout-card form') || document.querySelector('form');
        if (checkoutForm) {
            checkoutForm.addEventListener('submit', finalizarPedido);
        }

        // También conectar al botón tipo submit si lo hay
        const submitBtn = document.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.addEventListener('click', finalizarPedido);
        }
    });
