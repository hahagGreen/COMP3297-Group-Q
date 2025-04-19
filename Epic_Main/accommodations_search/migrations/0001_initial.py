# Generated by Django 5.1.7 on 2025-04-17 13:40

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
                ("availability_start", models.DateField()),
                ("availability_end", models.DateField()),
                ("type", models.CharField(max_length=20)),
                ("beds", models.PositiveIntegerField()),
                ("bedrooms", models.PositiveIntegerField()),
                ("price", models.FloatField()),
                ("building_name", models.CharField(max_length=255)),
                ("latitude", models.FloatField()),
                ("longitude", models.FloatField()),
                ("address", models.TextField()),
                ("geo_address", models.TextField(blank=True, null=True)),
                ("owner_name", models.CharField(max_length=255)),
                ("owner_contact", models.CharField(max_length=255)),
                ("is_reserved", models.BooleanField(default=False)),
                ("average_rating", models.FloatField(default=0)),
                ("rating_count", models.IntegerField(default=0)),
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
                ("comment", models.TextField(blank=True, null=True)),
                ("date", models.DateField()),
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
                            ("pending", "Pending"),
                            ("confirmed", "Confirmed"),
                            ("canceled", "Canceled"),
                            ("completed", "Completed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
            ],
            options={
                "db_table": "Reservation",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="Specialist",
            fields=[
                ("specialist_id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("password", models.CharField(max_length=255)),
                ("contact", models.CharField(max_length=255)),
            ],
            options={
                "db_table": "Specialist",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="Student",
            fields=[
                ("user_id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("password", models.CharField(max_length=255)),
                ("contact", models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                "db_table": "Student",
                "managed": False,
            },
        ),
    ]
