import csv
from urllib.parse import quote
from django.http import HttpResponse
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate, TruncMonth
import json
from .models import Producto, Orden, GananciaDiaria, GananciaMensual,Resena

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio_anterior', 'precio', 'stock', 'categoria', 'es_oferta')
    list_editable = ('precio_anterior', 'precio', 'stock', 'es_oferta') 
    list_filter = ('categoria', 'es_oferta')
    search_fields = ('nombre',)

@admin.register(Orden)
class OrdenAdmin(admin.ModelAdmin):
    list_display = ('id_con_estilo', 'fecha', 'cliente_info', 'metodo_entrega', 'entrega_detalle', 'pago_status', 'total_formateado', 'contactar_whatsapp')
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
    actions = ['marcar_como_pagado', 'marcar_como_entregado', 'exportar_a_csv']

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

    def contactar_whatsapp(self, obj):
        telefono_limpio = str(obj.telefono).replace(" ", "").replace("+", "")

        if not telefono_limpio.startswith("56"):
            telefono_limpio = "56" + telefono_limpio

        mensaje = f"Hola {obj.nombre}, te escribimos de Panadería La Jovita 🥖. ¡Tu pedido #{obj.id} ya está listo para ser retirado en el local!"
        mensaje_codificado = quote(mensaje)
        
        url = f"https://wa.me/{telefono_limpio}?text={mensaje_codificado}"

        return format_html(
            '<a class="btn btn-sm text-white shadow-sm" href="{}" target="_blank" style="background-color: #25D366; border-radius: 20px;">'
            '<i class="fab fa-whatsapp me-1"></i> Avisar'
            '</a>',
            url
        )
    contactar_whatsapp.short_description = "Aviso"

    def exportar_a_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reporte_ventas.csv"'
        response.write(u'\ufeff'.encode('utf8')) 

        writer = csv.writer(response, delimiter=';') 
        writer.writerow(['ID Orden', 'Fecha', 'Cliente', 'Email', 'Teléfono', 'Método', 'Total Pagado', 'Estado', 'Entregado', 'Productos'])

        for orden in queryset:
            fecha_str = orden.fecha.strftime("%d/%m/%Y %H:%M")
            estado_pago = "PAGADO" if orden.pagado else "POR COBRAR"
            estado_entrega = "SÍ" if orden.entregado else "NO"
            
            writer.writerow([
                orden.id,
                fecha_str,
                f"{orden.nombre} {orden.apellido}",
                orden.email,
                orden.telefono,
                orden.get_metodo_entrega_display(),
                orden.total,
                estado_pago,
                estado_entrega,
                orden.detalle_productos
            ])
            
        return response
    exportar_a_csv.short_description = "📥 Descargar reporte en Excel (CSV)"

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

        ventas_por_mes = (
            qs.annotate(mes=TruncMonth('fecha'))
            .values('mes')
            .annotate(total_ganado=Sum('total'), cantidad_ordenes=Count('id'))
            .order_by('-mes')
        )
        datos_grafico = list(ventas_por_mes[:12])
        datos_grafico.reverse()
        fechas_str = [v['mes'].strftime("%m/%Y") for v in datos_grafico if v['mes']]
        totales_num = [float(v['total_ganado']) for v in datos_grafico if v['total_ganado']]

        extra_context = extra_context or {
            "ventas_por_mes": ventas_por_mes,
            "fechas_json": json.dumps(fechas_str),
            "totales_json": json.dumps(totales_num),
        }

        return super().changelist_view(request, extra_context=extra_context)

@admin.register(Resena)
class ResenaAdmin(admin.ModelAdmin):
    list_display = ('producto', 'nombre_cliente', 'estrellas', 'fecha')
    list_filter = ('estrellas', 'producto')
    search_fields = ('nombre_cliente', 'comentario')