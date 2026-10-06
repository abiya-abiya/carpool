from django.http import JsonResponse
from .models import Ride


def index(request):
    """Health check and API overview."""
    return JsonResponse({
        'status': 'ok',
        'message': 'Carpool rides API and bot service is running.'
    })


def ride_list(request):
    """JSON view of active rides."""
    rides = Ride.objects.filter(status='ACTIVE', available_seats__gt=0).values(
        'id', 'driver_name', 'departure_location', 'arrival_location',
        'date', 'time', 'available_seats'
    )
    return JsonResponse({'rides': list(rides)})
