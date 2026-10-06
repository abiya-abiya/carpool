from django.contrib import admin
from .models import Ride, Booking


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'driver_name',
        'departure_location',
        'arrival_location',
        'date',
        'time',
        'available_seats',
        'status',
        'created_at',
    )
    list_filter = ('status', 'date', 'departure_location', 'arrival_location')
    search_fields = ('driver_name', 'driver_username', 'departure_location', 'arrival_location')
    date_hierarchy = 'date'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'ride',
        'passenger_name',
        'passenger_username',
        'seats_booked',
        'status',
        'created_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('passenger_name', 'passenger_username', 'ride__departure_location', 'ride__arrival_location')
