from celery import shared_task
from django.utils import timezone
from .models import Reservation

@shared_task
def expire_reservations():
    """Mark pending reservations as canceled after they expire."""
    
    expired = Reservation.objects.filter(
        status=Reservation.PENDING,
        created_at__lte=timezone.now() - timezone.timedelta(hours=24)  # 24-hour expiry
    ).update(status=Reservation.CANCELED)
    
    return f"Expired {expired} reservations"
