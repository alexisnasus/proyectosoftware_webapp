from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django import forms
from django.forms import ModelForm
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from .models import Producto, Seccion, Subseccion, Ubicacion, Inventario
from django.views.decorators.http import require_POST
from .forms import ProductoForm, InventarioFormSet
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required


def producto_list_ajax(request):
    query = request.GET.get('term', '')
    productos = Producto.objects.filter(
        Q(nombre__icontains=query) | Q(codigo_barras__icontains=query)
    ).select_related('seccion', 'subseccion').prefetch_related('inventarios__ubicacion')

    html = render_to_string('includes/product_list.html', {'productos': productos})
    return HttpResponse(html)

@login_required
@permission_required('inv.add_producto', raise_exception=True)
def producto_crear(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        inventario_formset = InventarioFormSet(request.POST, instance=Producto())
        if form.is_valid() and inventario_formset.is_valid():
            producto = form.save()
            inventario_formset.instance = producto
            inventario_formset.save()
            return JsonResponse({'success': True})
        else:
            errors = form.errors.as_json()
            formset_errors = inventario_formset.errors
            return JsonResponse({'success': False, 'errors': errors, 'formset_errors': formset_errors})
    else:
        form = ProductoForm()
        inventario_formset = InventarioFormSet()
    return render(request, 'includes/product_form.html', {'form': form, 'inventario_formset': inventario_formset})

@login_required
@permission_required('inv.change_producto', raise_exception=True)
def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        inventario_formset = InventarioFormSet(request.POST, instance=producto)
        if form.is_valid() and inventario_formset.is_valid():
            form.save()
            inventario_formset.save()
            return JsonResponse({'success': True})
        else:
            errors = form.errors.as_json()
            formset_errors = inventario_formset.errors
            return JsonResponse({'success': False, 'errors': errors, 'formset_errors': formset_errors})
    else:
        form = ProductoForm(instance=producto)
        inventario_formset = InventarioFormSet(instance=producto)
    return render(request, 'includes/product_form.html', {'form': form, 'inventario_formset': inventario_formset})

def producto_eliminar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.delete()
        return JsonResponse({'success': True})
    else:
        return render(request, 'includes/product_delete_confirm.html', {'producto': producto})

def producto_mover(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = MoverProductoForm(request.POST)
        if form.is_valid():
            ubicacion_origen = form.cleaned_data['ubicacion_origen']
            ubicacion_destino = form.cleaned_data['ubicacion_destino']
            cantidad = form.cleaned_data['cantidad']

            # Actualizar inventarios
            inventario_origen, created = Inventario.objects.get_or_create(
                producto=producto, ubicacion=ubicacion_origen, defaults={'cantidad': 0, 'cantidad_minima': 0}
            )
            inventario_destino, created = Inventario.objects.get_or_create(
                producto=producto, ubicacion=ubicacion_destino, defaults={'cantidad': 0, 'cantidad_minima': 0}
            )

            if inventario_origen.cantidad >= cantidad:
                inventario_origen.cantidad -= cantidad
                inventario_destino.cantidad += cantidad
                inventario_origen.save()
                inventario_destino.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'errors': 'Cantidad insuficiente en la ubicación de origen.'})
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'errors': errors})
    else:
        form = MoverProductoForm()
    return render(request, 'includes/move_product_form.html', {'form': form, 'producto': producto})


class ProductoForm(ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'codigo_barras', 'precio', 'seccion', 'subseccion']

class MoverProductoForm(forms.Form):
    ubicacion_origen = forms.ModelChoiceField(queryset=Ubicacion.objects.all())
    ubicacion_destino = forms.ModelChoiceField(queryset=Ubicacion.objects.all())
    cantidad = forms.IntegerField(min_value=1)


class ProductoListView(ListView):
    model = Producto
    template_name = 'producto_list.html'
    context_object_name = 'productos'
    
    def get_queryset(self):
        return Producto.objects.all().select_related('seccion', 'subseccion').prefetch_related('inventarios__ubicacion')

def buscar_productos(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        query = request.GET.get('term', '').strip()
        productos = Producto.objects.filter(
            Q(nombre__icontains=query) | Q(codigo_barras__icontains=query)
        ).select_related('seccion', 'subseccion').prefetch_related('inventarios__ubicacion')
        
        results = []
        for producto in productos:
            # Preparar la lista de ubicaciones
            ubicaciones = []
            for inventario in producto.inventarios.all():
                ubicaciones.append({
                    'nombre': inventario.ubicacion.nombre,
                    'cantidad': inventario.cantidad,
                })
            producto_json = {
                'id': producto.id,
                'nombre': producto.nombre,
                'codigo_barras': producto.codigo_barras,
                'precio': str(producto.precio),
                'existencias': producto.total_stock(),
                'seccion': producto.seccion.nombre if producto.seccion else '',
                'subseccion': producto.subseccion.nombre if producto.subseccion else '',
                'ubicaciones': ubicaciones,
            }
            results.append(producto_json)
        return JsonResponse(results, safe=False)
    return JsonResponse({'error': 'Error al procesar la solicitud.'}, status=400)

def buscar_productos_autocomplete(request):
    term = request.GET.get('term', '')
    productos = Producto.objects.filter(nombre__icontains=term)[:10]
    results = []
    for producto in productos:
        results.append({
            'id': producto.id,
            'nombre': producto.nombre,
            'precio': str(producto.precio),
        })
    return JsonResponse({'results': results})


