from django.db import models
from django.contrib.auth.models import AbstractUser

# Opcional: Extender el modelo de usuario de Django
class Usuario(AbstractUser):
    ROL_CHOICES = [
        ('Empleado', 'Empleado'),
        ('Jefe de Tienda', 'Jefe de Tienda'),
    ]
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='Empleado')

    def __str__(self):
        return self.username

class Seccion(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Subseccion(models.Model):
    nombre = models.CharField(max_length=100)
    seccion = models.ForeignKey(Seccion, on_delete=models.CASCADE, related_name='subsecciones')

    def __str__(self):
        return f"{self.seccion.nombre} - {self.nombre}"

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    codigo_barras = models.CharField(max_length=50, unique=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    seccion = models.ForeignKey(Seccion, on_delete=models.SET_NULL, null=True, related_name='productos')
    subseccion = models.ForeignKey(Subseccion, on_delete=models.SET_NULL, null=True, related_name='productos')

    def __str__(self):
        return self.nombre

    def total_stock(self):
        # Retorna la suma de las cantidades en todas las ubicaciones
        return sum(inventario.cantidad for inventario in self.inventarios.all())

class Ubicacion(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

class Inventario(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='inventarios')
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.CASCADE, related_name='inventarios')
    cantidad = models.IntegerField()
    cantidad_minima = models.IntegerField()

    class Meta:
        unique_together = ('producto', 'ubicacion')

    def __str__(self):
        return f"{self.producto.nombre} en {self.ubicacion.nombre}: {self.cantidad}"

    def check_stock(self):
        if self.cantidad <= self.cantidad_minima:
            # Generar una alerta si el stock es bajo en esta ubicación
            Alerta.objects.create(
                producto=self.producto,
                ubicacion=self.ubicacion,
                tipo_alerta='Stock Bajo',
                inventario=self,
            )

class Venta(models.Model):
    fecha_hora = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='ventas')
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Venta {self.id} - {self.fecha_hora}"

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.SET_NULL, null=True)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Detalle {self.id} - Venta {self.venta.id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Actualizar el stock del producto en la ubicación al guardar el detalle de venta
        inventario, created = Inventario.objects.get_or_create(
            producto=self.producto,
            ubicacion=self.ubicacion,
            defaults={'cantidad': 0, 'cantidad_minima': 0}
        )
        inventario.cantidad -= self.cantidad
        inventario.save()
        inventario.check_stock()

class Alerta(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='alertas')
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.CASCADE, related_name='alertas')
    inventario = models.ForeignKey(Inventario, on_delete=models.CASCADE, related_name='alertas')
    fecha_hora = models.DateTimeField(auto_now_add=True)
    tipo_alerta = models.CharField(max_length=50)
    resuelta = models.BooleanField(default=False)

    def __str__(self):
        return f"Alerta {self.tipo_alerta} - {self.producto.nombre} en {self.ubicacion.nombre}"

class Reporte(models.Model):
    TIPO_REPORTE_CHOICES = [
        ('diario', 'Diario'),
        ('semanal', 'Semanal'),
        ('mensual', 'Mensual'),
    ]
    tipo_reporte = models.CharField(max_length=20, choices=TIPO_REPORTE_CHOICES)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    fecha_generado = models.DateTimeField(auto_now_add=True)
    datos = models.JSONField()

    def __str__(self):
        return f"Reporte {self.tipo_reporte} - Generado el {self.fecha_generado}"
    
class Devolucion(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='devoluciones')
    detalle_venta = models.ForeignKey(DetalleVenta, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Actualizar el inventario
        inventario, created = Inventario.objects.get_or_create(
            producto=self.detalle_venta.producto,
            ubicacion=self.detalle_venta.ubicacion,
            defaults={'cantidad': 0, 'cantidad_minima': 0}
        )
        inventario.cantidad += self.cantidad
        inventario.save()
