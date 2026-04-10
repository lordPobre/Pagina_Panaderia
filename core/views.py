import mercadopago
import os
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import Producto,Orden

def home(request):
    # Traemos los productos normales (puedes excluir las ofertas si no quieres que se repitan)
    productos = Producto.objects.filter(es_oferta=False)
    
    # Traemos SOLO los productos que marcaste como oferta
    ofertas = Producto.objects.filter(es_oferta=True)
    
    return render(request, 'index.html', {
        'productos': productos,
        'ofertas': ofertas
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

    return redirect('home')

def ver_carrito(request):
    ids_carrito = request.session.get('carrito', [])
    
    # Usaremos un diccionario para agrupar los productos por su ID
    carrito_agrupado = {}
    total = 0
    
    for producto_id in ids_carrito:
        producto = Producto.objects.filter(id=producto_id).first()
        if producto:
            # Si el producto ya está en nuestro resumen, le sumamos 1 a la cantidad
            if producto.id in carrito_agrupado:
                carrito_agrupado[producto.id]['cantidad'] += 1
                carrito_agrupado[producto.id]['subtotal'] += producto.precio
            # Si es la primera vez que lo vemos, lo registramos con cantidad 1
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

    return render(request, 'carrito.html', {'items': items, 'total': total})

def restar_uno(request, producto_id):
    carrito = request.session.get('carrito', [])
    if producto_id in carrito:
        # remove() elimina solo la primera coincidencia que encuentra
        carrito.remove(producto_id)
        request.session['carrito'] = carrito
    return redirect('carrito')

def sumar_uno(request, producto_id):
    carrito = request.session.get('carrito', [])
    carrito.append(producto_id)
    request.session['carrito'] = carrito
    return redirect('carrito')

def eliminar_producto(request, producto_id):
    # Obtenemos el carrito actual
    carrito = request.session.get('carrito', [])
    
    # Si el producto está en el carrito, lo sacamos
    if producto_id in carrito:
        carrito.remove(producto_id)
        request.session['carrito'] = carrito # Guardamos el carrito actualizado
        
    # Recargamos la página del carrito
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
        hora_retiro = request.POST.get('hora_retiro') if metodo == 'retiro' else None
        metodo_pago = request.POST.get('metodo_pago')
        
        # 1. Armamos UN SOLO diccionario con todos los datos
        datos = {
            'nombre': nombre,
            'apellido': apellido,
            'email': email,
            'telefono': telefono,
            'direccion': direccion,
            'metodo_entrega': metodo,
            'hora_retiro': hora_retiro, # ¡Aquí viaja la hora a salvo!
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
        # 1. Agrupamos los IDs para calcular cantidades reales
        conteo_productos = {}
        for p_id in ids_carrito:
            conteo_productos[p_id] = conteo_productos.get(p_id, 0) + 1

        # 2. Calculamos el total y generamos el detalle con cantidades
        total = 0
        lista_nombres = []
        productos_db = Producto.objects.filter(id__in=conteo_productos.keys())

        for p in productos_db:
            cantidad = conteo_productos[str(p.id)] if str(p.id) in conteo_productos else conteo_productos.get(p.id, 0)
            subtotal = p.precio * cantidad
            total += subtotal
            lista_nombres.append(f"{cantidad}x {p.nombre}")

        detalle = ", ".join(lista_nombres)
        
        # 3. Preparamos datos finales seguros (usando .get() para evitar errores si algo falta)
        direccion_final = datos_cliente.get('direccion', '') if datos_cliente.get('metodo_entrega') == 'despacho' else "Retiro en local"
        pago_confirmado = (datos_cliente.get('metodo_pago') == 'mercadopago')

        # 4. Creamos la orden en la BD
        nueva_orden = Orden.objects.create(
            nombre=datos_cliente['nombre'],
            apellido=datos_cliente['apellido'],
            email=datos_cliente['email'],
            telefono=datos_cliente['telefono'],
            metodo_entrega=datos_cliente['metodo_entrega'],
            metodo_pago=datos_cliente['metodo_pago'],            
            direccion=direccion_final,  # <-- CORREGIDO: Ahora usa la variable calculada
            total=total,
            detalle_productos=detalle,
            pagado=pago_confirmado,     # <-- CORREGIDO: Ahora usa la variable calculada
            carrito_data=conteo_productos,
            hora_retiro=datos_cliente.get('hora_retiro')
        )

        # ==========================================
        # 5. ENVÍO DE CORREOS HTML (Cliente y Vendedor)
        # ==========================================
        try:
            # Diccionario que enviamos a las plantillas HTML
            contexto = {'orden': nueva_orden}

            # --- CORREO 1: AL CLIENTE ---
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

            # --- CORREO 2: AL VENDEDOR (ADMIN) ---
            html_vendedor = render_to_string('emails/vendedor.html', contexto)
            text_vendedor = strip_tags(html_vendedor)
            
            # El asunto te avisará de inmediato si es despacho o retiro
            tipo_entrega = 'RETIRO' if nueva_orden.metodo_entrega == 'retiro' else 'DESPACHO'
            asunto_vendedor = f"NUEVO PEDIDO: #{nueva_orden.id} - {tipo_entrega}"
            
            msg_vendedor = EmailMultiAlternatives(
                subject=asunto_vendedor,
                body=text_vendedor,
                from_email=settings.EMAIL_HOST_USER,
                to=[settings.EMAIL_HOST_USER] # Llega al correo configurado en settings
            )
            msg_vendedor.attach_alternative(html_vendedor, "text/html")
            msg_vendedor.send(fail_silently=False)
            
        except Exception as e:
            # Usamos un print para que si el correo falla en desarrollo (ej. mala contraseña), 
            # no se caiga la página y el cliente igual vea la pantalla de éxito.
            print(f"Error enviando correos: {e}")
        # ==========================================

        # 6. LIMPIEZA: Vaciamos el carrito y los datos temporales
        request.session['carrito'] = []
        request.session['datos_cliente'] = {} # <-- CORREGIDO: Mejor dejar un dict vacío que None
        request.session.modified = True
        
        return render(request, 'pago_exitoso.html', {'orden': nueva_orden})
    
    # Si alguien entra a la URL de éxito sin comprar, lo enviamos al inicio
    return redirect('home')