from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Producto, Transaccion, Item
from .serializers import ProductoSerializer, TransaccionSerializer
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

        try:
            producto = Producto.objects.get(codigo=codigo)
        except Producto.DoesNotExist:
            return Response({'error': 'Producto no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        # NOTA: Verificación de stock debe hacerse desde inventario
        # Aquí solo se registra el item en la transacción

        Item.objects.create(transaccion=transaccion, producto=producto, cantidad=cantidad)
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

        # Eliminar los ítems asociados (si deseas mantener historial, comenta esto)
        transaccion.item_set.all().delete()

        transaccion.estado = 'FALLIDA'
        transaccion.confirmado_en = timezone.now()
        transaccion.save()

        return Response({'mensaje': 'Transacción cancelada'}, status=200)
