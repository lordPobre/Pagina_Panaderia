from django.urls import path
from .views import reporte_ventas_json
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('nosotros/', views.nosotros, name='nosotros'),
    path('categoria/<str:nombre_cat>/', views.filtrar_categoria, name='filtrar_categoria'),
    path('carrito/', views.ver_carrito, name='carrito'),
    path('agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar'),
    path('vaciar/', views.vaciar_carrito, name='vaciar'),
    path('eliminar/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    path('checkout/', views.checkout, name='checkout'),
    path('pagar/', views.procesar_pago, name='procesar_pago'),
    path('restar/<int:producto_id>/', views.restar_uno, name='restar_uno'),
    path('sumar-uno/<int:producto_id>/', views.sumar_uno, name='sumar_uno'),
    path('buscar-ajax/', views.buscar_productos_ajax, name='buscar_ajax'),
    path('pago-exitoso/', views.pago_exitoso, name='pago_exitoso'),
    path('api/ventas-chart/', reporte_ventas_json, name='api_ventas_chart'),
    path('producto/<int:producto_id>/', views.producto_detalle, name='producto_detalle'),
    path('producto/<int:producto_id>/resena/', views.dejar_resena, name='dejar_resena')

]