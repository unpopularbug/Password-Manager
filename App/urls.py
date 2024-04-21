from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewset, LoginViewset, PasswordViewset, APIUserViewset

router = DefaultRouter()
router.register(r'accounts/signup', UserViewset, basename='Signup')
router.register(r'accounts/api/signup', APIUserViewset, basename='API-user-signup')
router.register(r'dashboard', PasswordViewset, basename='Dashboard')


urlpatterns = [
    path('', include(router.urls)),
    path('accounts/login/', LoginViewset.as_view(), name='Login'),
]