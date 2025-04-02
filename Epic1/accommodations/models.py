from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

# User model
class User(models.Model):
    STUDENT = 'Student'
    SPECIALIST = 'Specialist'
    ROLE_CHOICES = [
        (STUDENT, 'Student'),
        (SPECIALIST, 'Specialist'),
    ]

    user_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # Store hashed passwords
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    class Meta:
        db_table = 'User'  # Match the exact table name in your database
        managed = False   # Tell Django this table is managed externally

    def __str__(self):
        return self.name


# Accommodation model
class Accommodation(models.Model):
    accommodation_id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=100)
    availability_start = models.DateField()
    availability_end = models.DateField()
    beds = models.PositiveIntegerField()
    bedrooms = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    address = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    geo_address = models.TextField()
    is_reserved = models.BooleanField(default=False)

    class Meta:
        db_table = 'Accommodation'  # Match the exact table name in your database
        managed = False            # Tell Django this table is managed externally

    def __str__(self):
        return f"{self.type} at {self.address}"


# Reservation model
class Reservation(models.Model):
    TEMP = 'temp'
    CONFIRMED = 'confirmed'
    CANCELED = 'canceled'
    COMPLETED = 'completed'
    
    STATUS_CHOICES = [
        (TEMP, 'Temporary (2h)'),
        (CONFIRMED, 'Confirmed'),
        (CANCELED, 'Canceled'),
        (COMPLETED, 'Completed'),
    ]

    reservation_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    accommodation = models.ForeignKey(Accommodation, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=TEMP)  
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'Reservation'  # Match the exact table name in your database
        managed = False          # Tell Django this table is managed externally

    def save(self, *args, **kwargs):
        if self.status == self.TEMP and not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=24)
        if self.status == self.CONFIRMED:
            self.accommodation.is_reserved = True
            self.accommodation.save()
        elif self.status in [self.CANCELED, self.COMPLETED]:
            self.accommodation.is_reserved = False
            self.accommodation.save()
        
        super().save(*args, **kwargs)

    def is_active(self):
        return self.status == self.TEMP and timezone.now() < self.expires_at

    def __str__(self):
        return f"Reservation {self.reservation_id} - {self.get_status_display()}"

     

# Rating model
class Rating(models.Model):
    rating_id = models.AutoField(primary_key=True)
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])
    date = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'Rating'  # Match the exact table name in your database
        managed = False     # Tell Django this table is managed externally

    def __str__(self):
        return f"Rating {self.rating} for Reservation {self.reservation.reservation_id}"


# Campus model
class Campus(models.Model):
    campus_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        db_table = 'Campus'  # Match the exact table name in your database
        managed = False     # Tell Django this table is managed externally

    def __str__(self):
        return self.name