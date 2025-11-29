document.addEventListener('DOMContentLoaded', function () {
    lottie.loadAnimation({
        container: document.getElementById('lottie-animation-failure'),
        renderer: 'svg',
        loop: false,
        autoplay: true,
        // *** RUTA DIRECTA DE ARCHIVOS ESTATICOS DE DJANGO ***
        path: "/static/lottie/apps/modulos/pedidos/failed.json" 
    });
});