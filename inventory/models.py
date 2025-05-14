from django.db import models

class Item(models.Model):
    """
    Representa un artículo en el inventario.
    """
    name = models.CharField("Nombre", max_length=200)
    description = models.TextField("Descripción", blank=True)
    quantity = models.PositiveIntegerField("Stock", default=0)
    price = models.DecimalField("Precio unitario", max_digits=10, decimal_places=2)
    created_at = models.DateTimeField("Creado el", auto_now_add=True)
    updated_at = models.DateTimeField("Última actualización", auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Artículo"
        verbose_name_plural = "Artículos"

    def __str__(self):
        return f"{self.name} (Stock: {self.quantity})"
