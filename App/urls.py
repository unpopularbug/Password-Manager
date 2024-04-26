from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewset, LoginViewset, LogoutViewset, PasswordViewset, APIUserViewset, PasswordResetView, PasswordConfirmView

router = DefaultRouter()
router.register(r'accounts/api-user', APIUserViewset, basename='register api user')
router.register(r'dashboard/passwords', PasswordViewset, basename='passwords dashboard')


urlpatterns = [
    path('', include(router.urls)),
    path('accounts/user/', UserViewset.as_view({'post': 'register'}), name='register user'),
    path('accounts/user/<uuid:user_id>/confirm-code/', UserViewset.as_view({'post': 'confirm_code'}), name='confirm-code'),
    path('accounts/login/', LoginViewset.as_view(), name='login'),
    path('accounts/logout/', LogoutViewset.as_view(), name='logout'),
    path('accounts/reset-password/', PasswordResetView.as_view(), name='Reset password'),
    path('accounts/confirm-password-reset/', PasswordConfirmView.as_view(), name='Confirm password reset'),
]