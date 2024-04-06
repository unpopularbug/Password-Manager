import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


#pylint: disable=no-member
class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        user = self.model(
            email = self.normalize_email(email),
            password = password,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None):
        user = self.create_user(
            email = self.normalize_email(email),
            password = password,
        )
        user.is_admin = True
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        
        user.set_password(password)
        user.save(using=self._db)
        return user
    

class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    
    objects = UserManager()
    
    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        super().save(*args, **kwargs)
    
    def has_module_perms(self, app_label):
        return True
    
    def __str__(self):
        return f"{self.email}"
    
    
class Password(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=False, related_name='owner')
    site_name_or_url = models.CharField(max_length=255, null=True, blank=False)
    email_used = models.EmailField(null=True, blank=True)
    username_used = models.CharField(max_length=25, null=True, blank=True)
    password = models.CharField(max_length=128, null=True)
    
    def __str__(self):
        return f"{self.site_name_or_url} - {self.owner.email}"