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

    class Meta:
        verbose_name_plural = "Órdenes"
    
    def save(self, *args, **kwargs):
        descontar_stock = False

        if self.pk:
            # Si la orden YA existía, revisamos si acaba de ser pagada
            vieja_orden = Orden.objects.get(pk=self.pk)
            if not vieja_orden.pagado and self.pagado:
                descontar_stock = True
        else:
            # Si la orden es NUEVA y viene pagada de inmediato (MercadoPago)
            if self.pagado:
                descontar_stock = True

        # Guardamos la orden normalmente
        super().save(*args, **kwargs)

        # Si se confirmó el pago, descontamos el stock de la base de datos
        if descontar_stock and self.carrito_data:
            from .models import Producto # Importación local
            for p_id, cantidad in self.carrito_data.items():
                try:
                    producto = Producto.objects.get(id=int(p_id))
                    producto.stock -= cantidad
                    # Evitamos que el stock quede en números negativos
                    if producto.stock < 0:
                        producto.stock = 0
                    producto.save()
                except Producto.DoesNotExist:
                    pass

    def __str__(self):
        return f"Orden #{self.id} - {self.nombre} {self.apellido}"

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