from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from inv.models import Producto, Venta, DetalleVenta, Ubicacion, Inventario  # Importamos los modelos desde 'inv'

class NuevaVentaView(LoginRequiredMixin, View):
    def get(self, request):
        productos = Producto.objects.all()
        ubicaciones = Ubicacion.objects.all()
        return render(request, 'nueva_venta.html', {'productos': productos, 'ubicaciones': ubicaciones})

    def post(self, request):
        # Procesar la venta
        productos_ids = request.POST.getlist('producto')
        cantidades = request.POST.getlist('cantidad')
        ubicaciones_ids = request.POST.getlist('ubicacion')

        total = 0
        venta = Venta.objects.create(usuario=request.user, total=0)
        for producto_id, cantidad, ubicacion_id in zip(productos_ids, cantidades, ubicaciones_ids):
            producto = Producto.objects.get(id=producto_id)
            cantidad = int(cantidad)
            ubicacion = Ubicacion.objects.get(id=ubicacion_id)
            precio_unitario = producto.precio
            subtotal = precio_unitario * cantidad
            total += subtotal

            DetalleVenta.objects.create(
                venta=venta,
                producto=producto,
                ubicacion=ubicacion,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                subtotal=subtotal
            )

        venta.total = total
        venta.save()
        return redirect('ventas:venta_detalle', venta_id=venta.id)

class VentaDetalleView(LoginRequiredMixin, View):
    def get(self, request, venta_id):
        venta = Venta.objects.get(id=venta_id)
        return render(request, 'venta_detalle.html', {'venta': venta})
