import csv
import json
from urllib.parse import quote

from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate, TruncMonth
from django.utils.translation import gettext_lazy as _

from .models import Producto, Orden, GananciaDiaria, GananciaMensual, Resena, OrdenActiva, OrdenHistorial,ImagenProducto

class ImagenProductoInline(admin.TabularInline):
    model = ImagenProducto
    extra = 3  
    fields = ('imagen', 'orden')

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio_anterior', 'precio', 'stock', 'categoria', 'es_oferta')
    list_editable = ('precio_anterior', 'precio', 'stock', 'es_oferta') 
    list_filter = ('categoria', 'es_oferta')
    search_fields = ('nombre',)
    inlines = [ImagenProductoInline]

class BaseOrdenAdmin(admin.ModelAdmin):
    """Clase maestra que centraliza toda la lógica visual y de acciones"""
    
    list_display = (
        'id_con_estilo', 'fecha_pedido_formateada', 'fecha_retiro', 
        'entrega_detalle', 'cliente_info', 'pago_status', 
        'estado', 'total_formateado', 'contactar_whatsapp'
    )
    list_filter = ('estado', 'pagado', 'metodo_entrega', 'fecha_retiro', 'fecha')
    search_fields = ('id', 'nombre', 'apellido', 'email', 'telefono')
    readonly_fields = ('fecha', 'detalle_productos', 'total')
    date_hierarchy = 'fecha_retiro'
    ordering = ('-fecha',)
    actions = [
        'marcar_como_preparando', 
        'marcar_como_listo', 
        'marcar_como_entregado', 
        'marcar_como_pagado', 
        'exportar_a_csv'
    ]

    fieldsets = (
        ('Estado de la Venta', {
            'fields': ('estado', 'pagado', 'entregado', 'total', 'fecha')
        }),
        ('Información del Cliente', {
            'fields': (('nombre', 'apellido'), 'email', 'telefono')
        }),
        ('Detalles de Entrega y Productos', {
            'fields': ('metodo_entrega', 'metodo_pago', 'hora_retiro', 'fecha_retiro', 'direccion', 'detalle_productos'),
        }),
    )

    @admin.action(description="📦 Marcar como: En Preparación")
    def marcar_como_preparando(self, request, queryset):
        queryset.update(estado='preparando')
        self.message_user(request, "Órdenes actualizadas a: En Preparación")

    @admin.action(description="✅ Marcar como: Listo para entrega")
    def marcar_como_listo(self, request, queryset):
        queryset.update(estado='listo')
        self.message_user(request, "Órdenes actualizadas a: Listas")

    @admin.action(description="🏁 Marcar como: Entregado")
    def marcar_como_entregado(self, request, queryset):
        queryset.update(estado='entregado', entregado=True)
        self.message_user(request, "Órdenes marcadas como entregadas y movidas al historial.")

    @admin.action(description="💰 Marcar como: Pagado")
    def marcar_como_pagado(self, request, queryset):
        queryset.update(pagado=True)
        self.message_user(request, "Órdenes marcadas como pagadas.")

    @admin.display(description='Fecha Pedido', ordering='fecha')
    def fecha_pedido_formateada(self, obj):
        if obj.fecha:
            return timezone.localtime(obj.fecha).strftime("%d/%m/%Y %H:%M")
        return "-"

    def id_con_estilo(self, obj):
        return format_html('<span style="font-weight: bold; color: #2980b9;">#{}</span>', obj.id)

    def cliente_info(self, obj):
        return format_html('{} {}<br><small class="text-muted">{}</small>', 
                           obj.nombre, obj.apellido, obj.telefono)

    def pago_status(self, obj):
        if obj.pagado:
            return mark_safe('<span class="badge bg-success" style="padding: 5px 10px;">PAGADO</span>')
        return mark_safe('<span class="badge bg-danger" style="padding: 5px 10px;">POR COBRAR</span>')

    def entrega_detalle(self, obj):
        if obj.metodo_entrega == 'retiro' and obj.hora_retiro:
            return format_html(
                '<div style="background-color: #6f42c1; color: white; padding: 3px 8px; border-radius: 10px; font-size: 11px; display: inline-block;">'
                '<i class="fas fa-clock"></i> {}</div>',
                obj.hora_retiro.strftime("%H:%M")
            )
        return mark_safe('<span class="text-muted">Despacho</span>')

    def total_formateado(self, obj):
        if obj.total is not None:
            valor_con_puntos = "{:,}".format(int(obj.total)).replace(",", ".")
            return format_html('<strong>${}</strong>', valor_con_puntos)
        return "$0"
    total_formateado.short_description = "Total"

    def contactar_whatsapp(self, obj):
        tel = str(obj.telefono).replace(" ", "").replace("+", "")
        if not tel.startswith("56"): tel = "56" + tel
        msj = quote(f"Hola {obj.nombre}, ¡tu pedido #{obj.id} de La Jovita ya está listo! 🥖")
        url = f"https://wa.me/{tel}?text={msj}"
        return format_html(
            '<a class="btn btn-sm text-white shadow-sm" href="{}" target="_blank" style="background-color: #25D366; border-radius: 20px; padding: 2px 12px; font-size: 11px; text-decoration: none;">'
            '<i class="fab fa-whatsapp"></i> Avisar</a>', url
        )

    def exportar_a_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reporte_ventas.csv"'
        response.write(u'\ufeff'.encode('utf8')) 
        writer = csv.writer(response, delimiter=';') 
        writer.writerow(['ID', 'Fecha', 'Cliente', 'Método', 'Total', 'Pago', 'Estado', 'Productos'])
        for o in queryset:
            writer.writerow([o.id, o.fecha.strftime("%d/%m/%Y %H:%M"), f"{o.nombre} {o.apellido}", 
                             o.get_metodo_entrega_display(), o.total, "Pagado" if o.pagado else "Pendiente", 
                             o.estado, o.detalle_productos])
        return response
    exportar_a_csv.short_description = "📥 Exportar Excel (CSV)"

@admin.register(OrdenActiva)
class OrdenActivaAdmin(BaseOrdenAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).exclude(estado='entregado')

@admin.register(OrdenHistorial)
class OrdenHistorialAdmin(BaseOrdenAdmin):
    actions = ['exportar_a_csv', 'marcar_como_pagado']
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(estado='entregado')

    def has_add_permission(self, request): return False

@admin.register(GananciaDiaria)
class GananciaDiariaAdmin(admin.ModelAdmin):
    change_list_template = 'admin/ganancias_diarias.html' 
    def has_add_permission(self, request): return False
    def has_delete_permission(self, request, obj=None): return False
    def changelist_view(self, request, extra_context=None):
        qs = Orden.objects.filter(pagado=True)
        ventas = qs.annotate(dia=TruncDate('fecha')).values('dia').annotate(total=Sum('total'), cant=Count('id')).order_by('-dia')
        grafico = list(ventas[:7])
        grafico.reverse()
        context = {
            "ventas_por_dia": ventas,
            "fechas_json": json.dumps([v['dia'].strftime("%d/%m") for v in grafico if v['dia']]),
            "totales_json": json.dumps([float(v['total']) for v in grafico if v['total']]),
        }
        return super().changelist_view(request, extra_context={**extra_context, **context} if extra_context else context)

@admin.register(GananciaMensual)
class GananciaMensualAdmin(admin.ModelAdmin):
    change_list_template = 'admin/ganancias_mensuales.html'
    def has_add_permission(self, request): return False
    def has_delete_permission(self, request, obj=None): return False

    def changelist_view(self, request, extra_context=None):
        qs = Orden.objects.filter(pagado=True)
        ventas = qs.annotate(mes=TruncMonth('fecha')).values('mes').annotate(total=Sum('total'), cant=Count('id')).order_by('-mes')
        grafico = list(ventas[:12])
        grafico.reverse()
        context = {
            "ventas_por_mes": ventas,
            "fechas_json": json.dumps([v['mes'].strftime("%m/%Y") for v in grafico if v['mes']]),
            "totales_json": json.dumps([float(v['total']) for v in grafico if v['total']]),
        }
        return super().changelist_view(request, extra_context={**extra_context, **context} if extra_context else context)

@admin.register(Resena)
class ResenaAdmin(admin.ModelAdmin):
    list_display = ('producto', 'nombre_cliente', 'estrellas', 'fecha')
    list_filter = ('estrellas', 'producto')
    search_fields = ('nombre_cliente', 'comentario')