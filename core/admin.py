from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate,TruncMonth
import json
from .models import Producto,Orden,GananciaDiaria,GananciaMensual

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio_anterior', 'precio', 'stock', 'categoria', 'es_oferta')
    list_editable = ('precio_anterior', 'precio', 'stock', 'es_oferta') 
    list_filter = ('categoria', 'es_oferta')
    search_fields = ('nombre',)

@admin.register(Orden)
class OrdenAdmin(admin.ModelAdmin):
    list_display = ('id_con_estilo', 'fecha', 'cliente_info', 'metodo_entrega', 'entrega_detalle', 'pago_status', 'total_formateado')
    list_filter = ('entregado', 'pagado', 'metodo_entrega', 'fecha', 'metodo_pago')
    search_fields = ('nombre', 'apellido', 'email', 'telefono')
    fieldsets = (
        ('Estado de la Venta', {
            'fields': ('pagado', 'entregado', 'total') 
        }),
        ('Información del Cliente', {
            'fields': (('nombre', 'apellido'), 'email', 'telefono')
        }),
        ('Detalles de Entrega y Productos', {
            'fields': ('metodo_entrega', 'metodo_pago','hora_retiro', 'direccion', 'detalle_productos'),
            'classes': ('collapse',),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  
            return ('nombre', 'apellido', 'email', 'telefono', 'direccion', 'metodo_entrega', 'metodo_pago', 'hora_retiro', 'total', 'detalle_productos')
        return ()

    def id_con_estilo(self, obj):
        return format_html('<span style="font-weight: bold;">#{}</span>', obj.id)
    id_con_estilo.short_description = "Orden"

    def cliente_info(self, obj):
        return format_html('{} {}<br><small class="text-muted">{}</small>', 
                           obj.nombre, obj.apellido, obj.telefono)
    cliente_info.short_description = "Cliente"

    def pago_status(self, obj):
        if obj.pagado:
            return format_html('<span class="badge bg-success">{}</span>', 'PAGADO')
        return format_html('<span class="badge bg-danger">{}</span>', 'POR COBRAR')
    pago_status.short_description = "Pago"

    def entrega_status(self, obj):
        if obj.entregado:
            return format_html('<span class="badge bg-info text-dark"><i class="fas fa-check-double me-1"></i> {}</span>', 'ENTREGADO')
        return format_html('<span class="badge bg-warning text-dark"><i class="fas fa-box-open me-1"></i> {}</span>', 'PREPARANDO')
    entrega_status.short_description = "Estado Entrega"

    def entrega_detalle(self, obj):
        if obj.metodo_entrega == 'retiro' and obj.hora_retiro:
            return format_html(
                '<span class="badge bg-purple text-white" style="background-color: #6f42c1;">'
                '<i class="fas fa-clock me-1"></i> Retira a las: {}</span>',
                obj.hora_retiro.strftime("%H:%M")
            )
        return "N/A (Despacho)"
    entrega_detalle.short_description = "Detalle Retiro"
    
    def total_formateado(self, obj):
        return f"${obj.total:,}".replace(",", ".")
    total_formateado.short_description = "Total"

    actions = ['marcar_como_pagado', 'marcar_como_entregado']

    def marcar_como_pagado(self, request, queryset):
        contador = 0
        for orden in queryset:
            if not orden.pagado:
                orden.pagado = True
                orden.save() 
                contador += 1
        
        self.message_user(request, f"Se han marcado {contador} órdenes como pagadas y se ha descontado el stock.")
    marcar_como_pagado.short_description = "Marcar seleccionados como PAGADOS"

    def marcar_como_entregado(self, request, queryset):
        queryset.update(entregado=True)
    marcar_como_entregado.short_description = "Marcar seleccionados como ENTREGADOS"

@admin.register(GananciaDiaria)
class GananciaDiariaAdmin(admin.ModelAdmin):
    change_list_template = 'admin/ganancias_diarias.html' 

    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        qs = Orden.objects.filter(pagado=True)

        ventas_por_dia = (
            qs.annotate(dia=TruncDate('fecha'))
            .values('dia')
            .annotate(total_ganado=Sum('total'), cantidad_ordenes=Count('id'))
            .order_by('-dia')
        )
        datos_grafico = list(ventas_por_dia[:7])
        datos_grafico.reverse() 
        fechas_str = [v['dia'].strftime("%d/%m/%Y") for v in datos_grafico if v['dia']]
        totales_num = [float(v['total_ganado']) for v in datos_grafico if v['total_ganado']]

        extra_context = extra_context or {
            "ventas_por_dia": ventas_por_dia,
            "fechas_json": json.dumps(fechas_str),
            "totales_json": json.dumps(totales_num),
        }

        return super().changelist_view(request, extra_context=extra_context)

@admin.register(GananciaMensual)
class GananciaMensualAdmin(admin.ModelAdmin):
    change_list_template = 'admin/ganancias_mensuales.html'
    
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        qs = Orden.objects.filter(pagado=True)

        # Agrupamos matemáticamente por MES
        ventas_por_mes = (
            qs.annotate(mes=TruncMonth('fecha'))
            .values('mes')
            .annotate(total_ganado=Sum('total'), cantidad_ordenes=Count('id'))
            .order_by('-mes')
        )

        # Preparamos datos para el gráfico (Últimos 12 meses)
        datos_grafico = list(ventas_por_mes[:12])
        datos_grafico.reverse()

        # Formateamos la fecha a "Mes Año" (Ej: 04/2026)
        fechas_str = [v['mes'].strftime("%m/%Y") for v in datos_grafico if v['mes']]
        totales_num = [float(v['total_ganado']) for v in datos_grafico if v['total_ganado']]

        extra_context = extra_context or {
            "ventas_por_mes": ventas_por_mes,
            "fechas_json": json.dumps(fechas_str),
            "totales_json": json.dumps(totales_num),
        }

        return super().changelist_view(request, extra_context=extra_context)