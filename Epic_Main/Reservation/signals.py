# reservations/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Reservation, Student


@receiver(post_save, sender=Reservation)
def send_reservation_notification(sender, instance, **kwargs):
    """Send email notifications when a reservation is confirmed or canceled."""
    if instance.status in [Reservation.CONFIRMED, Reservation.CANCELED]:
        specialists = Student.objects.filter(role=Student.SPECIALIST)
        emails = [s.email for s in specialists]
        
        subject = f"Reservation {instance.reservation_id} {instance.get_status_display()}"
        message = f"""
        Reservation Details:
        User: {instance.user.name}
        Accommodation: {instance.accommodation.address}
        Status: {instance.get_status_display()}
        """
        
        send_mail(
            subject,
            message,
            'noreply@unihaven.com',
            emails,
            fail_silently=False,
        )
