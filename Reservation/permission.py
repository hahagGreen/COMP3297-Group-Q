# reservations/permissions.py
from rest_framework import permissions
from .models import User

class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == User.STUDENT

class IsSpecialist(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == User.SPECIALIST
