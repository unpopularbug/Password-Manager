from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewset, PasswordViewset

router = DefaultRouter()
router.register(r'accounts/user', UserViewset, basename='Create User')
router.register(r'home', PasswordViewset, basename='Passwords')

urlpatterns = [
    path('', include(router.urls)),
]