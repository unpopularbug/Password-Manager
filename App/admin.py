from django.contrib import admin
from .models import CustomUser, Password, ApiUser, APIKey

admin.site.register(CustomUser)
admin.site.register(Password)
admin.site.register(ApiUser)
admin.site.register(APIKey)