from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from inv.models import Producto, Venta, DetalleVenta, Ubicacion, Inventario, Devolucion
from decimal import Decimal


class NuevaVentaView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'inv.add_venta'
    def get(self, request):
        productos = Producto.objects.all()
        ubicaciones = Ubicacion.objects.all()
        return render(request, 'nueva_venta.html', {'productos': productos, 'ubicaciones': ubicaciones})

    def post(self, request):
        if 'confirmar' in request.POST:
            # El usuario ha confirmado la venta
            productos_ids = request.POST.getlist('producto')
            cantidades = request.POST.getlist('cantidad')
            ubicaciones_ids = request.POST.getlist('ubicacion')
            total = Decimal(request.POST.get('total'))
            venta = Venta.objects.create(usuario=request.user, total=total)
            for producto_id, cantidad, ubicacion_id in zip(productos_ids, cantidades, ubicaciones_ids):
                producto = Producto.objects.get(id=producto_id)
                cantidad = int(cantidad)
                ubicacion = Ubicacion.objects.get(id=ubicacion_id)
                precio_unitario = producto.precio
                subtotal = precio_unitario * cantidad

                # Crear el detalle de venta
                DetalleVenta.objects.create(
                    venta=venta,
                    producto=producto,
                    ubicacion=ubicacion,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    subtotal=subtotal
                )
            return redirect('ventas:venta_detalle', venta_id=venta.id)
        elif 'cancelar' in request.POST:
            # El usuario ha cancelado la venta
            return redirect('ventas:venta_nueva')
        else:
            # El usuario ha enviado el formulario por primera vez, mostrar resumen
            productos_ids = request.POST.getlist('producto')
            cantidades = request.POST.getlist('cantidad')
            ubicaciones_ids = request.POST.getlist('ubicacion')

            items = []
            total = 0
            for producto_id, cantidad, ubicacion_id in zip(productos_ids, cantidades, ubicaciones_ids):
                producto = Producto.objects.get(id=producto_id)
                cantidad = int(cantidad)
                ubicacion = Ubicacion.objects.get(id=ubicacion_id)
                precio_unitario = producto.precio
                subtotal = precio_unitario * cantidad
                total += subtotal
                items.append({
                    'producto': producto,
                    'cantidad': cantidad,
                    'ubicacion': ubicacion,
                    'precio_unitario': precio_unitario,
                    'subtotal': subtotal,
                })
            return render(request, 'confirmar_venta.html', {
                'items': items,
                'total': total,
                'productos_ids': productos_ids,
                'cantidades': cantidades,
                'ubicaciones_ids': ubicaciones_ids,
            })


class VentaDetalleView(LoginRequiredMixin, View):
    def get(self, request, venta_id):
        venta = Venta.objects.get(id=venta_id)
        return render(request, 'venta_detalle.html', {'venta': venta})
    
@login_required
@require_GET
def obtener_stock(request):
    producto_id = request.GET.get('producto_id')
    ubicacion_id = request.GET.get('ubicacion_id')

    try:
        inventario = Inventario.objects.get(producto_id=producto_id, ubicacion_id=ubicacion_id)
        cantidad = inventario.cantidad
    except Inventario.DoesNotExist:
        cantidad = 0  # Si no existe, asumimos que la cantidad es 0

    return JsonResponse({'cantidad': cantidad})


class DevolverProductoView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'inv.change_detalleventa'
    def get(self, request, detalle_venta_id):
        detalle = DetalleVenta.objects.get(id=detalle_venta_id)
        return render(request, 'devolver_producto.html', {'detalle': detalle})

    def post(self, request, detalle_venta_id):
        detalle = DetalleVenta.objects.get(id=detalle_venta_id)
        cantidad = int(request.POST.get('cantidad'))
        if 0 < cantidad <= detalle.cantidad:
            Devolucion.objects.create(
                venta=detalle.venta,
                detalle_venta=detalle,
                cantidad=cantidad,
            )
            # Actualizar el detalle de venta
            detalle.cantidad -= cantidad
            detalle.subtotal = detalle.cantidad * detalle.precio_unitario
            detalle.save()
            # Actualizar el total de la venta
            venta = detalle.venta
            venta.total -= cantidad * detalle.precio_unitario
            venta.save()
            return redirect('ventas:venta_detalle', venta_id=venta.id)
        else:
            error = 'Cantidad inválida'
            return render(request, 'devolver_producto.html', {'detalle': detalle, 'error': error})

