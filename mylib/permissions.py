import uuid
from rest_framework.permissions import BasePermission
from rest_framework import exceptions

from App.models import APIKey

#pylint: disable=no-member
class APIKeyPermission(BasePermission):
  def has_permission(self, request, view):
    key = request.headers.get('Authorization')
    if not key:
      raise exceptions.AuthenticationFailed('API key is required')
    
    try:
      uuid.UUID(key)
    except ValueError:
      raise exceptions.AuthenticationFailed('Invalid API key')

    try:
      api_key_obj = APIKey.objects.get(api_key=key)
    except APIKey.DoesNotExist:
      raise exceptions.AuthenticationFailed('Invalid API key')

    return True