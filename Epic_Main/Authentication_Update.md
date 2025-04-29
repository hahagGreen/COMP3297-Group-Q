## UniHaven Multi-University Extension Documentation

**Version:** 1.0
**Date:** April 29, 2025

### 1. Introduction

This document outlines the changes made to the UniHaven backend to support multiple universities (e.g., HKU, HKUST, CUHK) interacting with the system via its API. The core idea is to identify which university system is making an API request and tailor responses and actions accordingly.

### 2. Model Changes (`accommodations/models.py`)

* **New `University` Model:**
  * A new model `University` has been added to represent each participating university.
  * **Fields:**
    * `id`: Auto-incrementing primary key.
    * `name`: Unique character field for the university's name (e.g., 'HKU').
    * `api_key`: A unique, securely generated string used for authenticating API requests from the university's system. It defaults to a secure random string using `secrets.token_urlsafe`.
* **`Student` and Specialist Models Updated:**
  * A mandatory `university` ForeignKey field has been added to both `Student` and Specialist models.
  * This field links each student and specialist to their respective `University` record.
  * The previous `campus_id` field might need review or removal depending on whether the university affiliation replaces its role.

### 3. API Authentication (`unihaven/authentication.py` & settings.py)

* **`ApiKeyAuthentication` Backend:**
  * A custom Django REST Framework authentication backend (`ApiKeyAuthentication`) has been implemented in authentication.py.
  * **Mechanism:** It expects API clients (university systems) to include a custom HTTP header `X-API-Key` with their unique API key in every request.
  * **Validation:** The backend retrieves the key from the header, looks for a matching `api_key` in the `University` database table.
  * **Failure:** If the header is missing or the key is invalid, an `AuthenticationFailed` exception is raised (resulting in a 401 Unauthorized response).
  * **Success:** If the key is valid, the corresponding `University` object is fetched and attached to the Django request object as `request.university`. The authentication succeeds, returning `(None, api_key)`. We return `None` for the user part as this scheme authenticates the *system*, not an individual user login.
* **Integration:**
  * This new authentication backend has been added to `REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']` in settings.py. It will now be automatically checked for incoming API requests.

### 4. How to Use (For Developers)

* **Database Setup & Data Population:**

  * **Create Universities:** Ensure `University` records are created in the database for each participating university (HKU, HKUST, CUHK). You can do this manually via the Django admin interface or programmatically.
  * **API Keys:** Each `University` record will automatically get a secure API key upon creation (due to `default=secrets.token_urlsafe`). Securely share the appropriate `api_key` with the technical team responsible for each university's external system. **Treat these keys like passwords.**
  * **Update Data Scripts:** Modify create_db.py and makeupdata.py to:
    * Include the creation of `University` instances.
    * Associate newly created `Student` and Specialist records with the correct `University` instance using the `university_id` foreign key.
* **Modifying API Views:**

  * **Accessing Authenticated University:** Within any DRF API view (`APIView`, `ViewSet`, etc.), if the request was successfully authenticated using an API key, you can access the corresponding university object via `request.university`.

    ```python
    # Example inside an API view method (e.g., get, post)
    def get(self, request, *args, **kwargs):
        authenticated_university = getattr(request, 'university', None)
        if not authenticated_university:
            # Handle cases where authentication wasn't via API key
            # or failed (though DRF usually handles failure before view execution)
            return Response({"error": "University authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        # Now you can use authenticated_university
        print(f"Request received from: {authenticated_university.name}")
        # ... proceed with university-specific logic ...
    ```
  * **Filtering Data:** Use `request.university` to filter querysets. For example, when a student searches for accommodation, only show results offered by specialists from the *student's* university. When a specialist views listings, only show those associated with *their* university.

    ```python
    # Example: Search view filtering
    authenticated_university = request.university
    # Find specialists belonging to the authenticated university
    university_specialists = Specialist.objects.filter(university=authenticated_university)
    # Find offerings made by these specialists
    university_offerings = AccommodationOffering.objects.filter(specialist__in=university_specialists)
    # Get the accommodation IDs from these offerings
    accommodation_ids = university_offerings.values_list('accommodation_id', flat=True)
    # Filter accommodations
    queryset = Accommodation.objects.filter(accommodation_id__in=accommodation_ids)
    # ... apply other search filters ...
    ```
  * **Controlling Actions:** Ensure actions are performed within the correct university context.

    * **Reservations:** When a student makes a reservation, verify the chosen accommodation is offered by their university. Notify only specialists from that university.
    * **Adding Accommodation:** When a specialist adds accommodation, the associated `AccommodationOffering` implicitly links it to their university.

  * **Example: Viewing Active Reservations (`specialist/views.py`)**
    * The `api_view_active_reservations` view demonstrates how to use `request.university` along with the `IsAssociatedWithRequestUniversity` permission to fetch data relevant only to the requesting university.
    * It filters `Reservation` objects to show only those linked to accommodations offered by specialists from the university identified by the API key.

    ```python
    # In specialist/views.py
    from rest_framework.decorators import api_view, permission_classes
    from rest_framework.permissions import IsAuthenticated
    from unihaven.permissions import IsAssociatedWithRequestUniversity
    from .serializers import SpecialistReservationSerializer
    from .models import Specialist, AccommodationOffering, Reservation
    from rest_framework.response import Response

    @api_view(['GET'])
    @permission_classes([IsAuthenticated, IsAssociatedWithRequestUniversity])
    def api_view_active_reservations(request):
        """View Active Reservations, filtered by requesting university."""
        request_university = request.university # Guaranteed by IsAssociatedWithRequestUniversity

        university_specialists = Specialist.objects.filter(university=request_university)
        university_offerings = AccommodationOffering.objects.filter(specialist__in=university_specialists)
        accommodation_ids = university_offerings.values_list('accommodation_id', flat=True).distinct()
        active_reservations = Reservation.objects.filter(
            accommodation_id__in=accommodation_ids,
            status__in=[Reservation.PENDING, Reservation.CONFIRMED]
        )
        serializer = SpecialistReservationSerializer(active_reservations, many=True)
        return Response({'reservations': serializer.data})

    ```
* **Permissions (`unihaven/permissions.py`):**

  * **`IsAssociatedWithRequestUniversity` Permission Class:**

    * A custom DRF permission class has been created in permissions.py.
    * **Purpose:** This class ensures that API requests authenticated via `ApiKeyAuthentication` can only interact with objects (like `Reservations`, `Students`, `Specialists`, `AccommodationOfferings`) that are associated with the *same university* identified by the API key.
    * **Mechanism:**
      * It first checks if `request.university` exists (meaning the request was authenticated via API key).
      * For detail views (like retrieving or updating a specific reservation), it implements `has_object_permission`. This method checks the type of the object being accessed (`obj`) and compares its associated university with `request.university`.
        * For `Student` or Specialist objects, it checks `obj.university`.
        * For Reservation objects, it checks the university of the student who made the reservation (`obj.user.university`).
        * For `AccommodationOffering` objects, it checks the university of the specialist who created the offering (`obj.specialist.university`).
      * If the universities match, permission is granted; otherwise, it's denied (resulting in a 403 Forbidden response).
  * **Applying Permissions in Views:**

    * To use this permission, add it to the `permission_classes` list in your API views or viewsets.
    * It's often used alongside other permissions like `IsAuthenticated` (or DRF defaults).

    ```python
    # Example: Applying the permission to a detail view for Reservations
    # In Reservation/views.py

    from rest_framework import generics, permissions
    from .models import Reservation
    from .serializers import ReservationSerializer
    from unihaven.permissions import IsAssociatedWithRequestUniversity # Import the custom permission

    class ReservationDetailView(generics.RetrieveUpdateDestroyAPIView):
        queryset = Reservation.objects.all()
        serializer_class = ReservationSerializer
        # Apply the custom permission along with standard ones
        permission_classes = [permissions.IsAuthenticated, IsAssociatedWithRequestUniversity]
        # Ensure lookup field is set, e.g., lookup_field = 'reservation_id'

        # DRF handles checking has_object_permission automatically for detail views
    ```

    * For list views where you only want to show objects associated with the requesting university, you should primarily rely on filtering the queryset using `request.university` as shown previously. The `has_permission` check in `IsAssociatedWithRequestUniversity` ensures the request *comes* from an authenticated university system, but the filtering ensures *only relevant data* is returned.
* **Example API Request (Conceptual):**

  * A system representing HKUST would make a GET request like this (using `curl` as an example):
    ```bash
    curl -X GET "http://your-unihaven-domain.com/api/accommodations/search/?type=flat" \
         -H "X-API-Key: <HKUST_API_KEY_HERE>"
    ```
  * A system representing CUHK wanting to view its active reservations would make a GET request like this:
    ```bash
    curl -X GET "http://your-unihaven-domain.com/api/specialist/reservations/active/" \
         -H "X-API-Key: <CUHK_API_KEY_HERE>" \
         -H "Authorization: Bearer <Optional_User_Token_If_Needed>" # Depending on combined auth needs
    ```
    The `api_view_active_reservations` endpoint (assuming it's mapped to `/api/specialist/reservations/active/` in `specialist/urls.py`) would then use the `X-API-Key` to identify CUHK via `ApiKeyAuthentication`, check permissions with `IsAssociatedWithRequestUniversity`, and return only reservations linked to CUHK specialists.

### 5. Database Generation Changes

* **Updated Database Schema (`database/create_db.py`):**
  * The database creation script has been updated to include the new `University` table with fields:
    * `university_id` (PRIMARY KEY)
    * `name` (TEXT, NOT NULL, UNIQUE)
    * `country` (TEXT, NOT NULL)
    * `api_key` (TEXT, UNIQUE, NOT NULL)
  * Foreign key relationships have been updated in both the `Student` and `Specialist` tables to reference the `University` table.
  * The `Campus` table now includes a `university_id` field linking each campus to its university.
  * The `AccommodationOffering` table serves as an intermediary linking accommodations to specialists and campuses within a university context.

* **Sample Data Generation (`database/makeupdata.py`):**
  * The script now creates universities for HKU, HKUST, and CUHK with their respective campuses:
    ```python
    UNIVERSITIES = {
        "HKU": {
            "name": "University of Hong Kong",
            "country": "Hong Kong",
            "campuses": [
                ("Main Campus", 22.28405, 114.13784),
                # Additional campuses...
            ]
        },
        # HKUST and CUHK definitions...
    }
    ```
  * Secure API keys are automatically generated for each university using `secrets.token_urlsafe(32)`.
  * Students and specialists are distributed across universities and their campuses.
  * Accommodation offerings are created with respect to university boundaries, linking accommodations to specialists from the same university.
  * For a realistic scenario, 80% of student reservations are for accommodations within their own university, while 20% are for accommodations from other universities.
  * The script uses the updated database utility functions that now require university IDs:
    * `add_university(name, country, api_key)`
    * `add_campus(name, latitude, longitude, university_id)`
    * `register_student(name, email, password, contact, campus_id, university_id)`
    * `register_specialist(name, email, password, contact, campus_id, university_id)`
    * `add_accommodation_offering(accommodation_id, campus_id, specialist_id)`

* **Database Utilities (`database/dbutils.py`):**
  * All utility functions have been updated to support the multi-university schema.
  * New function `add_university()` has been added to create university records.
  * `add_campus()` now requires a `university_id` parameter.
  * User registration functions include university association.
  * `get_stats()` function now includes university statistics.
  * Foreign key validations ensure data integrity across university boundaries.

### 6. Next Steps

* **Run Migrations:** After these model changes, you **must** create and run database migrations:
  ```bash
  python manage.py makemigrations accommodations
  python manage.py migrate
  ```
* **Update Views and Serializers:** Systematically go through all relevant API views and serializers in accommodations, Reservation, and specialist apps to implement the university-specific logic (filtering, permissions, action constraints) as described above.
* **Testing:** Thoroughly test the API endpoints using different university API keys to ensure the logic works correctly.

---
