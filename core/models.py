from django.db import models

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=50, choices=[
        ('Panadería', 'Panadería'),
        ('Pastelería', 'Pastelería'),
        ('Empanadas', 'Empanadas'),
    ])
    precio = models.IntegerField()
    precio_anterior = models.IntegerField(null=True, blank=True)
    stock = models.IntegerField(default=0)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    es_oferta = models.BooleanField(default=False, verbose_name="¿Es oferta del día?")

    def __str__(self):
        return self.nombre

class Orden(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    direccion = models.TextField()
    total = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    fecha_retiro = models.DateField(null=True, blank=True, verbose_name="Fecha de Retiro")
    hora_retiro = models.TimeField(null=True, blank=True, verbose_name="Hora de Retiro")
    pagado = models.BooleanField(default=False)
    carrito_data = models.JSONField(default=dict, blank=True, null=True)
    detalle_productos = models.TextField() 
    hora_retiro = models.TimeField(null=True, blank=True, verbose_name="Hora de Retiro")
    entregado = models.BooleanField(default=False, verbose_name="Entregado")

    METODOS = [
        ('despacho', 'Despacho a Domicilio'),
        ('retiro', 'Retiro en Local (Av. Providencia 1234)')
    ]
    metodo_entrega = models.CharField(max_length=20, choices=METODOS, default='despacho')

    METODOS_PAGO = [
        ('mercadopago', 'MercadoPago (Online)'),
        ('presencial', 'Pago en Local'),
    ]
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default='mercadopago')

    ESTADOS_PEDIDO = [
        ('recibido', '📝 Recibido'),
        ('preparando', '👩‍🍳 En Preparación'),
        ('listo', '🛍️ Listo / En Camino'),
        ('entregado', '✅ Entregado')
    ]
    
    # Añade este campo a la clase Orden
    estado = models.CharField(max_length=20, choices=ESTADOS_PEDIDO, default='recibido')

    class Meta:
        verbose_name_plural = "Órdenes"
    
    def save(self, *args, **kwargs):
        descontar_stock = False

        if self.pk:
            vieja_orden = Orden.objects.get(pk=self.pk)
            if not vieja_orden.pagado and self.pagado:
                descontar_stock = True
        else:
            if self.pagado:
                descontar_stock = True

        super().save(*args, **kwargs)

        if descontar_stock and self.carrito_data:
            from .models import Producto 
            for p_id, cantidad in self.carrito_data.items():
                try:
                    producto = Producto.objects.get(id=int(p_id))
                    producto.stock -= cantidad
                    if producto.stock < 0:
                        producto.stock = 0
                    producto.save()
                except Producto.DoesNotExist:
                    pass

    def __str__(self):
        return f"Orden #{self.id} - {self.nombre} {self.apellido}"

# core/models.py
class Resena(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='resenas')
    nombre_cliente = models.CharField(max_length=100, verbose_name="Tu Nombre")
    comentario = models.TextField(verbose_name="Tu Comentario")
    estrellas = models.IntegerField(default=5, choices=[(i, i) for i in range(1, 6)], verbose_name="Calificación")
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Reseña"
        verbose_name_plural = "Reseñas"

    def __str__(self):
        return f"{self.nombre_cliente} sobre {self.producto.nombre}"

class GananciaDiaria(Orden):
    class Meta:
        proxy = True
        verbose_name = "Ganancia Diaria"
        verbose_name_plural = "Reporte de Ganancias"

class GananciaMensual(Orden):
    class Meta:
        proxy = True
        verbose_name = "Ganancia Mensual"
        verbose_name_plural = "Reporte Mensual"