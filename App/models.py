import uuid
import random
import string
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from cryptography.fernet import Fernet

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
    first_name = models.CharField(max_length=10, null=True, blank=True)
    last_name = models.CharField(max_length=10, null=True, blank=True)

    is_active = models.BooleanField(default=False)
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
    application_name = models.CharField(max_length=255, null=True, blank=False)
    site_url = models.CharField(max_length=255, null=True, blank=True)
    email_used = models.EmailField(null=True, blank=True)
    username_used = models.CharField(max_length=255, null=True, blank=True)
    password = models.CharField(max_length=128, null=True)
    decryption_key = models.BinaryField(null=True)
    
    def save(self, *args, **kwargs):
        if not self.decryption_key:
            fernet_key = Fernet.generate_key()
            self.decryption_key = fernet_key
        super().save(*args, **kwargs)


class VerificationCode(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='verification_code')
    code = models.CharField(unique=True, max_length=6)
    created_at = models.DateTimeField(default=timezone.now)

    @classmethod
    def create_unique_code(cls):
        """Generate a unique 6-digit code."""
        return ''.join(random.choices(string.digits, k=6))

    @classmethod
    def create(cls, user):
        """Create a new PasswordResetCode instance with a unique code."""
        code = cls.create_unique_code()
        return cls.objects.create(user=user, code=code)
    
    @classmethod
    def delete_expired_codes(cls):
        """Delete verification codes older than 5 minutes."""
        five_minutes_ago = timezone.now() - timezone.timedelta(minutes=5)
        expired_codes = cls.objects.filter(created_at__lt=five_minutes_ago)
        expired_codes.delete()
        
        
class PasswordResetCode(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reset_codes')
    code = models.CharField(unique=True, max_length=6)
    created_at = models.DateTimeField(default=timezone.now)

    @classmethod
    def create_unique_code(cls):
        """Generate a unique 6-digit code."""
        return ''.join(random.choices(string.digits, k=6))

    @classmethod
    def create(cls, user):
        """Create a new PasswordResetCode instance with a unique code."""
        code = cls.create_unique_code()
        return cls.objects.create(user=user, code=code)
    
    @classmethod
    def delete_expired_codes(cls):
        """Delete reset codes older than 5 minutes."""
        five_minutes_ago = timezone.now() - timezone.timedelta(minutes=5)
        expired_codes = cls.objects.filter(created_at__lt=five_minutes_ago)
        expired_codes.delete()
    
    
class ApiUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=25, null=False, blank=False)
    last_name = models.CharField(max_length=25, null=False, blank=False)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(validators=[phone_regex], max_length=17, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        related_name='api_user',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        Group,
        verbose_name=_('user permissions'),
        blank=True,
        related_name='api_user_set',
        related_query_name='user',
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    def has_module_perms(self, app_label):
        return True
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    
class APIKey(models.Model):
    owner = models.ForeignKey(ApiUser, on_delete=models.CASCADE, null=False, blank=False)
    api_key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.owner.first_name} - Key: {self.api_key}"