import mercadopago
import os
from django.http import JsonResponse
from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.utils.timezone import now
from datetime import timedelta
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import Producto,Orden,Resena
from django.shortcuts import render
from .models import Producto

def home(request):

    todas_las_ofertas = Producto.objects.filter(es_oferta=True).order_by('-id')
    oferta_principal = todas_las_ofertas.first()
    ofertas_secundarias = list(todas_las_ofertas[1:3])
    
    if len(ofertas_secundarias) < 2:
        extra = Producto.objects.filter(es_oferta=False).order_by('?')[:2 - len(ofertas_secundarias)]
        ofertas_secundarias.extend(list(extra))

    return render(request, 'index.html', {
        'oferta_principal': oferta_principal,
        'destacado_1': ofertas_secundarias[0] if len(ofertas_secundarias) > 0 else None,
        'destacado_2': ofertas_secundarias[1] if len(ofertas_secundarias) > 1 else None,
        'todas_las_ofertas': todas_las_ofertas, # <-- Esto es lo que activa el carrusel de abajo
    })

def nosotros(request):
    return render(request, 'nosotros.html')

def filtrar_categoria(request, nombre_cat):
    productos_filtrados = Producto.objects.filter(categoria=nombre_cat)
    return render(request, 'index.html', {'productos': productos_filtrados})

def agregar_al_carrito(request, producto_id):

    cantidad = int(request.POST.get('cantidad', 1))
    carrito = request.session.get('carrito', [])
    for _ in range(cantidad):
        carrito.append(producto_id)
    request.session['carrito'] = carrito
    url_anterior = request.META.get('HTTP_REFERER', '/')
    return redirect(url_anterior)

def ver_carrito(request):
    ids_carrito = request.session.get('carrito', [])   
    carrito_agrupado = {}
    total = 0
    
    for producto_id in ids_carrito:
        producto = Producto.objects.filter(id=producto_id).first()
        if producto:
            if producto.id in carrito_agrupado:
                carrito_agrupado[producto.id]['cantidad'] += 1
                carrito_agrupado[producto.id]['subtotal'] += producto.precio
            else:
                carrito_agrupado[producto.id] = {
                    'id': producto.id,
                    'nombre': producto.nombre,
                    'categoria': producto.categoria,
                    'precio_unitario': producto.precio,
                    'cantidad': 1,
                    'subtotal': producto.precio,
                    'imagen_url': producto.imagen.url if producto.imagen else '' 
                }
            total += producto.precio

    items = list(carrito_agrupado.values())

    categorias_en_carrito = Producto.objects.filter(id__in=ids_carrito).values_list('categoria', flat=True)
    sugerencias = Producto.objects.exclude(id__in=ids_carrito).exclude(categoria__in=categorias_en_carrito).filter(stock__gt=0)[:3]
    
    if not sugerencias:
        sugerencias = Producto.objects.exclude(id__in=ids_carrito).filter(stock__gt=0)[:3]

    meta_envio = 15000 
    falta_para_envio = max(0, meta_envio - total)
    
    if total == 0:
        progreso_envio = 0
    else:
        progreso_envio = min(100, (total / meta_envio) * 100)

    return render(request, 'carrito.html', {
        'items': items, 
        'total': total,
        'sugerencias': sugerencias,
        'falta_para_envio': falta_para_envio,
        'progreso_envio': progreso_envio
    })

def restar_uno(request, producto_id):
    carrito = request.session.get('carrito', [])
    if producto_id in carrito:
        carrito.remove(producto_id)
        request.session['carrito'] = carrito
    return redirect('carrito')

def sumar_uno(request, producto_id):
    carrito = request.session.get('carrito', [])
    carrito.append(producto_id)
    request.session['carrito'] = carrito
    return redirect('carrito')

def eliminar_producto(request, producto_id):
    carrito = request.session.get('carrito', [])

    if producto_id in carrito:
        carrito.remove(producto_id)
        request.session['carrito'] = carrito 

    return redirect('carrito')

def vaciar_carrito(request):
    if 'carrito' in request.session:
        del request.session['carrito']
    return redirect('carrito')

def checkout(request):
    if not request.session.get('carrito'):
        return redirect('home')
    return render(request, 'checkout.html')

def procesar_pago(request):
    if request.method == "POST":

        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')
        metodo = request.POST.get('metodo_entrega')
        fecha_retiro = request.POST.get('fecha_retiro') if metodo == 'retiro' else None
        hora_retiro = request.POST.get('hora_retiro') if metodo == 'retiro' else None
        
        metodo_pago = request.POST.get('metodo_pago')
        
        datos = {
            'nombre': nombre,
            'apellido': apellido,
            'email': email,
            'telefono': telefono,
            'direccion': direccion,
            'metodo_entrega': metodo,
            'fecha_retiro': fecha_retiro, # --- AGREGADO ---
            'hora_retiro': hora_retiro, 
            'metodo_pago': metodo_pago
        }

        request.session['datos_cliente'] = datos

        if datos['metodo_pago'] == 'presencial':
            return redirect('pago_exitoso')

        sdk = mercadopago.SDK(os.getenv('MP_ACCESS_TOKEN'))

        ids_carrito = request.session.get('carrito', [])
        if not ids_carrito:
            return redirect('carrito')

        carrito_agrupado = {}
        for producto_id in ids_carrito:
            producto = Producto.objects.filter(id=producto_id).first()
            if producto:
                if producto.id in carrito_agrupado:
                    carrito_agrupado[producto.id]['quantity'] += 1
                else:
                    carrito_agrupado[producto.id] = {
                        "id": str(producto.id),
                        "title": producto.nombre,
                        "quantity": 1,
                        "unit_price": float(producto.precio), 
                        "currency_id": "CLP"
                    }

        items_mp = list(carrito_agrupado.values())

        preference_data = {
            "items": items_mp,
            "payer": {
                "name": str(nombre),
                "surname": str(apellido),
                "email": str(email),
                "phone": {"number": str(telefono)},
                "address": {"street_name": str(direccion)}
            },
            "back_urls": {
                "success": "http://localhost:8000/pago-exitoso/",
                "failure": "http://localhost:8000/carrito/",
                "pending": "http://localhost:8000/pago-exitoso/"
            },
        }

        preference_response = sdk.preference().create(preference_data)

        if preference_response["status"] in [200, 201]:
            return redirect(preference_response["response"]["init_point"])
        else:
            return HttpResponse(f"Error de MercadoPago: {preference_response.get('response')}")
                    
    return redirect('checkout')

def pago_exitoso(request):
    datos_cliente = request.session.get('datos_cliente')
    ids_carrito = request.session.get('carrito', [])
    
    if datos_cliente and ids_carrito:
        conteo_productos = {}
        for p_id in ids_carrito:
            conteo_productos[p_id] = conteo_productos.get(p_id, 0) + 1

        total = 0
        lista_nombres = []
        productos_db = Producto.objects.filter(id__in=conteo_productos.keys())

        for p in productos_db:
            cantidad = conteo_productos[str(p.id)] if str(p.id) in conteo_productos else conteo_productos.get(p.id, 0)
            subtotal = p.precio * cantidad
            total += subtotal
            lista_nombres.append(f"{cantidad}x {p.nombre}")

        detalle = ", ".join(lista_nombres)
        direccion_final = datos_cliente.get('direccion', '') if datos_cliente.get('metodo_entrega') == 'despacho' else "Retiro en local"
        pago_confirmado = (datos_cliente.get('metodo_pago') == 'mercadopago')

        fecha_ret = datos_cliente.get('fecha_retiro')
        hora_ret = datos_cliente.get('hora_retiro')
        
        if not fecha_ret: fecha_ret = None
        if not hora_ret: hora_ret = None

        nueva_orden = Orden.objects.create(
            nombre=datos_cliente['nombre'],
            apellido=datos_cliente['apellido'],
            email=datos_cliente['email'],
            telefono=datos_cliente['telefono'],
            metodo_entrega=datos_cliente['metodo_entrega'],
            metodo_pago=datos_cliente['metodo_pago'],            
            direccion=direccion_final,  
            total=total,
            detalle_productos=detalle,
            pagado=pago_confirmado,     
            carrito_data=conteo_productos,
            fecha_retiro=fecha_ret,
            hora_retiro=hora_ret
        )
        nueva_orden.refresh_from_db() 

        try:
            dominio = request.build_absolute_uri('/')[:-1]
            contexto = {
                'orden': nueva_orden,
                'productos_comprados': productos_db,
                'dominio': dominio
            }

            html_cliente = render_to_string('emails/cliente.html', contexto)
            text_cliente = strip_tags(html_cliente)
            
            msg_cliente = EmailMultiAlternatives(
                subject=f'Confirmación de tu pedido #{nueva_orden.id} - Panadería',
                body=text_cliente,
                from_email=settings.EMAIL_HOST_USER,
                to=[nueva_orden.email]
            )
            msg_cliente.attach_alternative(html_cliente, "text/html")
            msg_cliente.send(fail_silently=False)

            # Correo Vendedor
            html_vendedor = render_to_string('emails/vendedor.html', contexto)
            text_vendedor = strip_tags(html_vendedor)
            tipo_entrega = 'RETIRO' if nueva_orden.metodo_entrega == 'retiro' else 'DESPACHO'
            asunto_vendedor = f"NUEVO PEDIDO: #{nueva_orden.id} - {tipo_entrega}"
            
            msg_vendedor = EmailMultiAlternatives(
                subject=asunto_vendedor,
                body=text_vendedor,
                from_email=settings.EMAIL_HOST_USER,
                to=[settings.EMAIL_HOST_USER] 
            )
            msg_vendedor.attach_alternative(html_vendedor, "text/html")
            msg_vendedor.send(fail_silently=False)
            
        except Exception as e:
            print(f"Error enviando correos: {e}")

        request.session['carrito'] = []
        request.session['datos_cliente'] = {} 
        request.session['orden_activa'] = nueva_orden.id 
        request.session.modified = True
        
        return render(request, 'pago_exitoso.html', {'orden': nueva_orden})
    
    return redirect('home')

def buscar_productos_ajax(request):
    query = request.GET.get('term', '')
    productos = Producto.objects.filter(nombre__icontains=query)[:5]
    results = []
    for p in productos:
        results.append({
            'id': p.id,
            'label': p.nombre,
            'value': p.nombre,
            'url': f"/agregar/{p.id}/" 
        })
    return JsonResponse(results, safe=False)

def reporte_ventas_json(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'No autorizado'}, status=403)

    hace_7_dias = now().date() - timedelta(days=7)
    ventas_7_dias = Orden.objects.filter(fecha__gte=hace_7_dias, pagado=True).annotate(
        dia=TruncDate('fecha')).values('dia').annotate(total_dia=Sum('total')).order_by('dia')

    total_mes = Orden.objects.filter(
        fecha__month=now().month, 
        fecha__year=now().year, 
        pagado=True
    ).aggregate(Sum('total'))['total__sum'] or 0
    pendientes = Orden.objects.filter(pagado=True, entregado=False).count()
    fechas = [v['dia'].strftime('%d/%m') for v in ventas_7_dias]
    totales = [v['total_dia'] for v in ventas_7_dias]

    return JsonResponse({
        'fechas': fechas, 
        'totales': totales,
        'total_mes': f"{total_mes:,}".replace(",", "."), 
        'pendientes': pendientes
    })

def producto_detalle(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    resenas = producto.resenas.all().order_by('-fecha')
    return render(request, 'producto_detalle.html', {
        'producto': producto,
        'resenas': resenas
    })

def dejar_resena(request, producto_id):
    if request.method == "POST":
        producto = get_object_or_404(Producto, id=producto_id)
        nombre = request.POST.get('nombre')
        comentario = request.POST.get('comentario')
        estrellas = request.POST.get('estrellas')

        Resena.objects.create(
            producto=producto,
            nombre_cliente=nombre,
            comentario=comentario,
            estrellas=estrellas
        )
        return redirect('producto_detalle', producto_id=producto.id)
    return redirect('home')

# core/views.py

def catalogo(request):
    categoria_slug = request.GET.get('categoria')
    
    if categoria_slug:
        productos = Producto.objects.filter(categoria__iexact=categoria_slug)
    else:
        productos = Producto.objects.all()

    return render(request, 'catalogo.html', {
        'productos': productos,
        'categoria_seleccionada': categoria_slug # Pasamos el nombre para el banner
    })

def rastreo_pedido(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)
    pesos = {
        'recibido': 15,
        'preparando': 50,
        'listo': 85,
        'entregado': 100
    }
    progreso = pesos.get(orden.estado, 15)

    return render(request, 'rastreo.html', {
        'orden': orden,
        'progreso': progreso
    })