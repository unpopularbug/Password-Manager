from django.contrib import admin
from .models import CustomUser, Password, APIUser, APIKey

admin.site.register(CustomUser)
admin.site.register(Password)
admin.site.register(APIUser)
admin.site.register(APIKey)