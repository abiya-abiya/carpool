from django.db import models, transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


class Ride(models.Model):
    """
    Model representing a carpool ride offered by a driver.
    """
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('FULL', 'Full'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    # Driver can be associated with a Django User and/or Telegram account
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='offered_rides',
        null=True,
        blank=True,
        help_text="Django user account if registered in web portal"
    )
    driver_telegram_id = models.BigIntegerField(
        db_index=True,
        help_text="Telegram User ID of the driver"
    )
    driver_name = models.CharField(
        max_length=255,
        help_text="Display name or full name of driver"
    )
    driver_username = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Telegram @username of driver without @"
    )

    # Locations
    departure_location = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="Departure Location",
        help_text="City or pickup address"
    )
    arrival_location = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="Arrival Location",
        help_text="City or drop-off address"
    )

    # Schedule
    date = models.DateField(
        db_index=True,
        verbose_name="Ride Date"
    )
    time = models.TimeField(
        verbose_name="Ride Departure Time"
    )

    # Capacity
    available_seats = models.PositiveIntegerField(
        default=1,
        verbose_name="Available Seats"
    )
    total_seats = models.PositiveIntegerField(
        default=1,
        verbose_name="Initial Total Seats"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'time']
        verbose_name = "Ride"
        verbose_name_plural = "Rides"

    def __str__(self):
        return (
            f"Ride #{self.pk}: {self.departure_location} -> {self.arrival_location} "
            f"on {self.date} at {self.time.strftime('%H:%M')} "
            f"({self.available_seats} seats left)"
        )

    def has_available_seats(self, seats: int = 1) -> bool:
        """Check if requested number of seats are available."""
        return self.status == 'ACTIVE' and self.available_seats >= seats


class Booking(models.Model):
    """
    Model linking rides and passengers with approval status.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]

    ride = models.ForeignKey(
        Ride,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    passenger = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='passenger_bookings',
        null=True,
        blank=True,
        help_text="Django user account if registered in web portal"
    )
    passenger_telegram_id = models.BigIntegerField(
        db_index=True,
        help_text="Telegram User ID of the passenger"
    )
    passenger_name = models.CharField(
        max_length=255,
        help_text="Display name or full name of passenger"
    )
    passenger_username = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Telegram @username of passenger without @"
    )

    seats_booked = models.PositiveIntegerField(
        default=1,
        verbose_name="Seats Booked"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"

    def __str__(self):
        return (
            f"Booking #{self.pk} for Ride #{self.ride_id} by "
            f"{self.passenger_name} ({self.status})"
        )

    @transaction.atomic
    def approve(self):
        """
        Approve the booking and decrease available seats on the ride.
        """
        if self.status != 'PENDING':
            raise ValidationError(f"Cannot approve booking with status '{self.status}'.")

        # Lock ride row for update to prevent race conditions
        ride = Ride.objects.select_for_update().get(pk=self.ride_id)
        if ride.available_seats < self.seats_booked:
            raise ValidationError("Not enough seats available on this ride.")

        ride.available_seats -= self.seats_booked
        if ride.available_seats == 0:
            ride.status = 'FULL'
        ride.save()

        self.status = 'APPROVED'
        self.save()
        return self

    @transaction.atomic
    def reject(self):
        """
        Reject the booking request.
        """
        if self.status != 'PENDING':
            raise ValidationError(f"Cannot reject booking with status '{self.status}'.")

        self.status = 'REJECTED'
        self.save()
        return self
