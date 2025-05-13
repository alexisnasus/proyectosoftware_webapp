from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['POST'])
def process_sale(request):
    # Simulación de transacción
    return Response({
        "status": "success",
        "message": "Venta simulada correctamente"
    })