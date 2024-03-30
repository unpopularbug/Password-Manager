from django.contrib import admin
from .models import CustomUser, Password

admin.site.register(CustomUser)
admin.site.register(Password)