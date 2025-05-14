from django.db import models
from inventory.models import Item

class Sale(models.Model):
    """
    Representa una venta de uno o varios artículos.
    """
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        related_name='sales',
        verbose_name="Artículo vendido"
    )
    quantity = models.PositiveIntegerField("Cantidad vendida")
    sale_price = models.DecimalField(
        "Precio de venta",
        max_digits=10,
        decimal_places=2,
        help_text="Precio por unidad en el momento de la venta"
    )
    sold_at = models.DateTimeField("Fecha de venta", auto_now_add=True)

    class Meta:
        ordering = ['-sold_at']
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"

    def __str__(self):
        return f"{self.quantity}×{self.item.name} el {self.sold_at:%Y-%m-%d %H:%M}"
