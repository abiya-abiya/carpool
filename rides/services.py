"""
Database service functions for aiogram bot interactions with Django ORM.
Uses sync_to_async to safely perform database operations within async event loops.
"""

from datetime import datetime, date as date_type, time as time_type
from typing import List, Optional, Tuple, Dict, Any
from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Ride, Booking


@sync_to_async
def create_ride_record(
    driver_telegram_id: int,
    driver_name: str,
    driver_username: Optional[str],
    departure: str,
    arrival: str,
    ride_date: date_type,
    ride_time: time_type,
    seats: int
) -> Ride:
    """Create and persist a new Ride offered by a driver."""
    return Ride.objects.create(
        driver_telegram_id=driver_telegram_id,
        driver_name=driver_name,
        driver_username=driver_username or '',
        departure_location=departure.strip(),
        arrival_location=arrival.strip(),
        date=ride_date,
        time=ride_time,
        available_seats=seats,
        total_seats=seats,
        status='ACTIVE'
    )


@sync_to_async
def get_available_rides(
    departure_query: Optional[str] = None,
    arrival_query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for active rides with available seats.
    Optionally filter by departure and/or arrival keywords (case-insensitive substring).
    """
    qs = Ride.objects.filter(status='ACTIVE', available_seats__gt=0)
    if departure_query:
        qs = qs.filter(departure_location__icontains=departure_query.strip())
    if arrival_query:
        qs = qs.filter(arrival_location__icontains=arrival_query.strip())

    rides_data = []
    for r in qs.order_by('date', 'time')[:20]:
        rides_data.append({
            'id': r.id,
            'driver_telegram_id': r.driver_telegram_id,
            'driver_name': r.driver_name,
            'driver_username': r.driver_username,
            'departure_location': r.departure_location,
            'arrival_location': r.arrival_location,
            'date': r.date,
            'time': r.time,
            'available_seats': r.available_seats,
            'total_seats': r.total_seats,
            'status': r.status,
        })
    return rides_data


@sync_to_async
def get_ride_details(ride_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve details for a specific ride."""
    try:
        r = Ride.objects.get(pk=ride_id)
        return {
            'id': r.id,
            'driver_telegram_id': r.driver_telegram_id,
            'driver_name': r.driver_name,
            'driver_username': r.driver_username,
            'departure_location': r.departure_location,
            'arrival_location': r.arrival_location,
            'date': r.date,
            'time': r.time,
            'available_seats': r.available_seats,
            'total_seats': r.total_seats,
            'status': r.status,
        }
    except Ride.DoesNotExist:
        return None


@sync_to_async
def create_booking_request(
    ride_id: int,
    passenger_telegram_id: int,
    passenger_name: str,
    passenger_username: Optional[str],
    seats_booked: int = 1
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Create a new booking request in PENDING status.
    Returns (success, message, booking_dict).
    """
    try:
        ride = Ride.objects.get(pk=ride_id)
    except Ride.DoesNotExist:
        return False, "Ride does not exist or has been deleted.", None

    if ride.status != 'ACTIVE' or ride.available_seats < seats_booked:
        return False, "Sorry, there are not enough available seats for this ride.", None

    if ride.driver_telegram_id == passenger_telegram_id:
        return False, "You cannot book your own ride!", None

    # Check if passenger already has a pending or approved booking
    existing = Booking.objects.filter(
        ride=ride,
        passenger_telegram_id=passenger_telegram_id,
        status__in=['PENDING', 'APPROVED']
    ).first()
    if existing:
        return False, f"You already have a {existing.status.lower()} booking for this ride.", None

    booking = Booking.objects.create(
        ride=ride,
        passenger_telegram_id=passenger_telegram_id,
        passenger_name=passenger_name,
        passenger_username=passenger_username or '',
        seats_booked=seats_booked,
        status='PENDING'
    )

    data = {
        'id': booking.id,
        'ride_id': ride.id,
        'driver_telegram_id': ride.driver_telegram_id,
        'departure': ride.departure_location,
        'arrival': ride.arrival_location,
        'date': str(ride.date),
        'time': ride.time.strftime('%H:%M'),
        'passenger_name': booking.passenger_name,
        'passenger_username': booking.passenger_username,
        'passenger_telegram_id': booking.passenger_telegram_id,
        'seats_booked': booking.seats_booked,
        'status': booking.status,
    }
    return True, "Booking request created successfully.", data


@sync_to_async
def process_driver_approval(booking_id: int, approved: bool) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Handle driver approval or rejection of a booking.
    Returns (success, message, updated_booking_dict).
    """
    try:
        booking = Booking.objects.select_related('ride').get(pk=booking_id)
    except Booking.DoesNotExist:
        return False, "Booking not found.", None

    if booking.status != 'PENDING':
        return False, f"This booking is already marked as {booking.status}.", None

    try:
        if approved:
            booking.approve()
            action_desc = "approved"
        else:
            booking.reject()
            action_desc = "rejected"
    except ValidationError as e:
        return False, str(e), None
    except Exception as e:
        return False, f"Failed to process booking: {str(e)}", None

    data = {
        'id': booking.id,
        'ride_id': booking.ride_id,
        'departure': booking.ride.departure_location,
        'arrival': booking.ride.arrival_location,
        'date': str(booking.ride.date),
        'time': booking.ride.time.strftime('%H:%M'),
        'remaining_seats': booking.ride.available_seats,
        'passenger_telegram_id': booking.passenger_telegram_id,
        'passenger_name': booking.passenger_name,
        'passenger_username': booking.passenger_username,
        'status': booking.status,
    }
    return True, f"Booking #{booking.id} was successfully {action_desc}.", data
