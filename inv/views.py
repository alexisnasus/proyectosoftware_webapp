from django.shortcuts import render
from django.views.generic import ListView
from django.http import JsonResponse
from django.db.models import Q

from .models import Producto

class ProductoListView(ListView):
    model = Producto
    template_name = 'producto_list.html'
    context_object_name = 'productos'
    
    def get_queryset(self):
        # Utilizar prefetch_related para optimizar las consultas
        return Producto.objects.all().prefetch_related('inventarios')

def buscar_productos(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        query = request.GET.get('term', '').strip()
        productos = Producto.objects.filter(
            Q(nombre__icontains=query) | Q(codigo_barras__icontains=query)
        ).distinct()

        results = []
        for producto in productos:
            producto_json = {
                'id': producto.id,
                'nombre': producto.nombre,
                'codigo_barras': producto.codigo_barras,
                'precio': str(producto.precio),
                'stock': producto.total_stock(),  # Añadimos las existencias
            }
            results.append(producto_json)
        return JsonResponse(results, safe=False)
    return JsonResponse({'error': 'Error al procesar la solicitud.'}, status=400)

