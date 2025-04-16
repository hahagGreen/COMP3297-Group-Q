# Generated by Django 5.1.7 on 2025-04-15 13:53

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Accommodation",
            fields=[
                (
                    "accommodation_id",
                    models.AutoField(primary_key=True, serialize=False),
                ),
                ("type", models.CharField(max_length=100)),
                ("availability_start", models.DateField()),
                ("availability_end", models.DateField()),
                ("beds", models.PositiveIntegerField()),
                ("bedrooms", models.PositiveIntegerField()),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("address", models.TextField()),
                ("latitude", models.FloatField()),
                ("longitude", models.FloatField()),
                ("geo_address", models.TextField()),
                ("is_reserved", models.BooleanField(default=False)),
            ],
            options={
                "db_table": "Accommodation",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="Campus",
            fields=[
                ("campus_id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("latitude", models.FloatField()),
                ("longitude", models.FloatField()),
            ],
            options={
                "db_table": "Campus",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="Rating",
            fields=[
                ("rating_id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "rating",
                    models.IntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(5),
                        ]
                    ),
                ),
                ("date", models.DateField(auto_now_add=True)),
            ],
            options={
                "db_table": "Rating",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="Reservation",
            fields=[
                ("reservation_id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("temp", "Temporary (2h)"),
                            ("confirmed", "Confirmed"),
                            ("canceled", "Canceled"),
                            ("completed", "Completed"),
                        ],
                        default="temp",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
            ],
            options={
                "db_table": "Reservation",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                ("user_id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("password", models.CharField(max_length=255)),
                (
                    "role",
                    models.CharField(
                        choices=[("Student", "Student"), ("Specialist", "Specialist")],
                        max_length=20,
                    ),
                ),
            ],
            options={
                "db_table": "User",
                "managed": False,
            },
        ),
    ]
