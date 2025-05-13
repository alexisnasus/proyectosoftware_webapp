from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def get_products(request):
    # Mock data para demostración
    return Response({
        "products": [
            {"id": 1, "name": "Producto Demo", "price": 100, "stock": 10}
        ]
    })