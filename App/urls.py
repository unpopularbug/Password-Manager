from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewset, LoginViewset, LogoutViewset, PasswordViewset, APIUserViewset, PasswordResetView, PasswordConfirmView

router = DefaultRouter()
router.register(r'accounts/user', UserViewset, basename='custom user')
router.register(r'accounts/api-user', APIUserViewset, basename='api user')
router.register(r'dashboard/passwords', PasswordViewset, basename='dashboard')


urlpatterns = [
    path('', include(router.urls)),
    path('accounts/login/', LoginViewset.as_view(), name='login'),
    path('accounts/logout/', LogoutViewset.as_view(), name='logout'),
    path('accounts/reset-password/', PasswordResetView.as_view(), name='Reset password'),
    path('accounts/confirm-password-reset/', PasswordConfirmView.as_view(), name='Confirm password reset'),
]