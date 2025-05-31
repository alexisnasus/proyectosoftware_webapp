from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Producto, Transaccion, Item
from .serializers import ProductoSerializer, TransaccionSerializer, AplicarDescuentoSerializer
from django.utils import timezone

class ProductoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    lookup_field = 'codigo'

class TransaccionViewSet(viewsets.ModelViewSet):
    queryset = Transaccion.objects.all()
    serializer_class = TransaccionSerializer

    @action(detail=True, methods=['post'])
    def agregar_item(self, request, pk=None):
        transaccion = self.get_object()
        codigo = request.data.get('codigo')
        cantidad = int(request.data.get('cantidad', 1))
        descuento = float(request.data.get('descuento', 0))

        try:
            producto = Producto.objects.get(codigo=codigo)
        except Producto.DoesNotExist:
            return Response({'error': 'Producto no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        if descuento < 0 or descuento > producto.precio:
            return Response({'error': 'Descuento inválido'}, status=status.HTTP_400_BAD_REQUEST)

        Item.objects.create(
            transaccion=transaccion,
            producto=producto,
            cantidad=cantidad,
            descuento=descuento
        )
        return Response(self.get_serializer(transaccion).data)

    @action(detail=True, methods=['post'])
    def aplicar_descuento(self, request, pk=None):
        transaccion = self.get_object()
        serializer = AplicarDescuentoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tipo = serializer.validated_data['tipo']
        valor = serializer.validated_data['valor']
        producto_id = serializer.validated_data.get('producto_id')

        items = transaccion.item_set.all()
        if producto_id:
            items = items.filter(producto_id=producto_id)

        if tipo == 'porcentaje':
            if valor > 100:
                return Response({'error': 'El porcentaje no puede ser mayor a 100'}, status=400)
            for item in items:
                item.descuento = item.producto.precio * (valor / 100)
                item.save()
        else:
            if valor <= 0:
                return Response({'error': 'El monto debe ser positivo'}, status=400)
            if producto_id and items.exists():
                item = items.first()
                if valor > item.producto.precio:
                    return Response({'error': 'El descuento no puede ser mayor al precio'}, status=400)
                item.descuento = valor
                item.save()
            elif not producto_id:
                total_transaccion = sum(item.producto.precio * item.cantidad for item in items)
                if valor > total_transaccion:
                    return Response({'error': 'El descuento no puede ser mayor al total'}, status=400)
                for item in items:
                    proporcion = (item.producto.precio * item.cantidad) / total_transaccion
                    item.descuento = (valor * proporcion) / item.cantidad
                    item.save()

        return Response(self.get_serializer(transaccion).data)

    @action(detail=True, methods=['post'])
    def confirmar(self, request, pk=None):
        transaccion = self.get_object()
        exito = request.data.get('exito', True)
        transaccion.estado = 'CONFIRMADA' if exito else 'FALLIDA'
        transaccion.confirmado_en = timezone.now()
        transaccion.save()
        return Response(self.get_serializer(transaccion).data)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        transaccion = self.get_object()

        if transaccion.estado != 'PENDIENTE':
            return Response({'error': 'Solo se pueden cancelar transacciones pendientes'}, status=400)

        transaccion.item_set.all().delete()
        transaccion.estado = 'FALLIDA'
        transaccion.confirmado_en = timezone.now()
        transaccion.save()

        return Response({'mensaje': 'Transacción cancelada'}, status=200)