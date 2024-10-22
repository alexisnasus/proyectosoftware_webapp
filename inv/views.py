from django.shortcuts import render
from django.views.generic import ListView
from django.http import JsonResponse
from django.db.models import Q
from django.db.models import Sum
from .models import Producto, Ubicacion, Inventario
from django.db.models import Sum,Prefetch
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json

@login_required
@require_POST
def actualizar_existencias(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        cantidad = data.get('cantidad')
        accion = data.get('accion')

        try:
            producto = Producto.objects.get(id=product_id)
            # Obtenemos o creamos el inventario para una ubicación predeterminada
            ubicacion, created = Ubicacion.objects.get_or_create(nombre='Almacén Principal')
            inventario, created = Inventario.objects.get_or_create(
                producto=producto,
                ubicacion=ubicacion,
                defaults={'cantidad': 0, 'cantidad_minima': 0}
            )

            if accion == 'agregar':
                inventario.cantidad += cantidad
            elif accion == 'quitar':
                if inventario.cantidad >= cantidad:
                    inventario.cantidad -= cantidad
                else:
                    return JsonResponse({'success': False, 'error': 'No hay suficientes existencias para quitar esa cantidad.'})
            else:
                return JsonResponse({'success': False, 'error': 'Acción no válida.'})

            inventario.save()
            # Recalcular el total de existencias
            nuevo_stock = producto.total_stock()
            return JsonResponse({'success': True, 'nuevo_stock': nuevo_stock})
        except Producto.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Producto no encontrado.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Solicitud inválida.'})

class ProductoListView(ListView):
    model = Producto
    template_name = 'producto_list.html'
    context_object_name = 'productos'

    def get_queryset(self):
        return Producto.objects.annotate(
            total_stock=Sum('inventarios__cantidad')
        ).prefetch_related(
            Prefetch('inventarios', queryset=Inventario.objects.select_related('ubicacion'))
        )



def buscar_productos(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        query = request.GET.get('term', '').strip()
        productos = Producto.objects.filter(
            Q(nombre__icontains=query) | Q(codigo_barras__icontains=query)
        ).annotate(
            total_stock=Sum('inventarios__cantidad')
        ).prefetch_related(
            Prefetch('inventarios', queryset=Inventario.objects.select_related('ubicacion'))
        ).distinct()

        results = []
        for producto in productos:
            ubicaciones = []
            for inventario in producto.inventarios.all():
                ubicaciones.append({
                    'ubicacion': inventario.ubicacion.nombre,
                    'cantidad': inventario.cantidad
                })
            producto_json = {
                'id': producto.id,
                'nombre': producto.nombre,
                'codigo_barras': producto.codigo_barras,
                'precio': str(producto.precio),
                'stock': producto.total_stock or 0,
                'ubicaciones': ubicaciones
            }
            results.append(producto_json)
        return JsonResponse(results, safe=False)
    return JsonResponse({'error': 'Error al procesar la solicitud.'}, status=400)



