from django.contrib import admin
from .models import MetodoEnvio, DireccionEnvio, Pedido, DetallePedido


@admin.register(MetodoEnvio)
class MetodoEnvioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo_transporte', 'costo', 'dias_estimados', 'activo', 'creado_en')
    list_filter = ('activo', 'creado_en')
    search_fields = ('nombre', 'tipo_transporte')
    ordering = ('nombre',)
    readonly_fields = ('creado_en', 'actualizado_en')
    
    fieldsets = (
        ('Información General', {
            'fields': ('nombre', 'tipo_transporte', 'descripcion')
        }),
        ('Detalles de Envío', {
            'fields': ('costo', 'dias_estimados', 'activo')
        }),
        ('Auditoría', {
            'fields': ('creado_en', 'actualizado_en'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DireccionEnvio)
class DireccionEnvioAdmin(admin.ModelAdmin):
    list_display = ('nombre_receptor', 'calle', 'ciudad', 'provincia', 'codigo_postal', 'creado_en')
    list_filter = ('provincia', 'pais', 'creado_en')
    search_fields = ('nombre_receptor', 'calle', 'ciudad')
    readonly_fields = ('creado_en', 'actualizado_en')


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'estado', 'tipo_transporte', 'total', 'creado_en')
    list_filter = ('estado', 'tipo_transporte', 'creado_en')
    search_fields = ('usuario__username', 'referencia_envio', 'referencia_reserva_stock')
    readonly_fields = ('creado_en', 'actualizado_en', 'confirmado_en')
    
    fieldsets = (
        ('Información del Pedido', {
            'fields': ('usuario', 'estado', 'tipo_transporte', 'total')
        }),
        ('Direcciones y Referencias', {
            'fields': ('direccion_envio', 'referencia_envio', 'referencia_reserva_stock')
        }),
        ('Auditoría', {
            'fields': ('creado_en', 'actualizado_en', 'confirmado_en'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DetallePedido)
class DetallePedidoAdmin(admin.ModelAdmin):
    list_display = ('pedido', 'nombre_producto', 'cantidad', 'precio_unitario', 'precio_total', 'creado_en')
    list_filter = ('pedido', 'creado_en')
    search_fields = ('nombre_producto', 'pedido__id')
    readonly_fields = ('creado_en', 'actualizado_en', 'precio_total')
