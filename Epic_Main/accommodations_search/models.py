from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Student(models.Model):
    user_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    contact = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'Student'
        managed = False

    def __str__(self):
        return self.name


class Specialist(models.Model):
    specialist_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    contact = models.CharField(max_length=255)

    class Meta:
        db_table = 'Specialist'
        managed = False

    def __str__(self):
        return self.name


class Accommodation(models.Model):
    accommodation_id = models.AutoField(primary_key=True)
    specialist = models.ForeignKey(
        Specialist, on_delete=models.SET_NULL, null=True, db_column='specialist_id'
    )
    availability_start = models.DateField()
    availability_end = models.DateField()
    type = models.CharField(max_length=20)
    beds = models.PositiveIntegerField()
    bedrooms = models.PositiveIntegerField()
    price = models.FloatField()
    building_name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.TextField()
    geo_address = models.TextField(null=True, blank=True)
    owner_name = models.CharField(max_length=255)
    owner_contact = models.CharField(max_length=255)
    is_reserved = models.BooleanField(default=False)
    average_rating = models.FloatField(default=0)
    rating_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'Accommodation'
        managed = False

    def __str__(self):
        return f"{self.type} at {self.building_name}"


class Reservation(models.Model):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELED = 'canceled'
    COMPLETED = 'completed'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (CONFIRMED, 'Confirmed'),
        (CANCELED, 'Canceled'),
        (COMPLETED, 'Completed'),
    ]

    reservation_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        Student, on_delete=models.CASCADE, db_column='user_id'
    )
    accommodation = models.ForeignKey(
        Accommodation, on_delete=models.CASCADE, db_column='accommodation_id'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)

    class Meta:
        db_table = 'Reservation'
        managed = False

    def __str__(self):
        return f"Reservation {self.reservation_id} - {self.get_status_display()}"


class Rating(models.Model):
    rating_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        Student, on_delete=models.CASCADE, db_column='user_id'
    )
    accommodation = models.ForeignKey(
        Accommodation, on_delete=models.CASCADE, db_column='accommodation_id'
    )
    rating = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])
    comment = models.TextField(null=True, blank=True)
    date = models.DateField()

    class Meta:
        db_table = 'Rating'
        managed = False

    def __str__(self):
        return f"Rating {self.rating} for {self.accommodation}"


class Campus(models.Model):
    campus_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        db_table = 'Campus'
        managed = False

    def __str__(self):
        return self.name