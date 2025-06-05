# /backend/ventas/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser

#
# --- Modelo de usuario personalizado (sin cambios) ---
#
class User(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('EMPLOYEE', 'Empleado'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, null=False, blank=False)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


#
# --- Producto y Stock (sin cambios) ---
#
class Producto(models.Model):
    codigo = models.CharField(max_length=100, unique=True, blank=True, null=True)
    nombre = models.CharField(max_length=300)
    # precio = models.DecimalField(max_digits=10, decimal_places=2) decimales
    precio = models.IntegerField()    # Antes DecimalField; ahora IntegerField

    
    class Meta:
        db_table = 'producto'

    def __str__(self):
        return f"{self.codigo} – {self.nombre}"


class Stock(models.Model):
    producto = models.OneToOneField(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=0)

    class Meta:
        db_table = 'stock'

    def __str__(self):
        return f"Stock({self.producto.codigo}): {self.cantidad}"


#
# --- Transacción (antes “carrito”) con DESCUENTO A NIVEL GLOBAL ---
#
class Transaccion(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('FALLIDA',   'Fallida'),
    ]
    # ¡Elimina la definición de UUID! Django usará un AutoField por defecto.
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    creado_en = models.DateTimeField(auto_now_add=True)
    confirmado_en = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='PENDIENTE')
    descuento_carrito = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = 'transaccion'

    @property
    def total(self):
        return sum(item.subtotal for item in self.item_set.all())

    @property
    def total_final(self):
        return self.total - self.descuento_carrito


#
# --- Ítem de la transacción (antes tenía campo 'descuento', que ahora removemos) ---
#
class Item(models.Model):
    transaccion = models.ForeignKey(Transaccion, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'item'

    @property
    def subtotal(self):
        """
        Precio a pagar por este ítem: (precio unitario * cantidad).
        El descuento ya se aplica únicamente a nivel de Transaccion.descuento_carrito,
        así que aquí no descontamos nada.
        """
        return self.producto.precio * self.cantidad

    def __str__(self):
        return f"{self.producto.codigo} x{self.cantidad} (Transacción {self.transaccion.id})"
