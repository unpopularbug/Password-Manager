from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewset, LoginViewset, PasswordViewset

router = DefaultRouter()
router.register(r'account/new-user', UserViewset, basename='Create User')
# router.register(r'account/login', LoginViewset, basename='User Login')
router.register(r'dashboard', PasswordViewset, basename='Dashboard')


urlpatterns = [
    path('', include(router.urls)),
    path('account/login/', LoginViewset.as_view()),
]