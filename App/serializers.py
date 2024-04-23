from rest_framework import serializers
from django.contrib.auth import authenticate

from .models import CustomUser, Password, ApiUser, APIKey

#pylint: disable=no-member
class UserSerializer(serializers.ModelSerializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def create(self, validated_data):
        user = CustomUser.objects.create(
            email = validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
    
    class Meta:
        model = CustomUser
        fields = ["id", "email", "first_name", "last_name", "password"]

        
class APIUserSerializer(serializers.ModelSerializer):
    email = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def create(self, validated_data):
        user = ApiUser.objects.create(
            email = validated_data['email'],
            first_name = validated_data['first_name'],
            last_name = validated_data['last_name'],
            phone_number = validated_data['phone_number'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
    
    class Meta:
        model = ApiUser
        fields = ["id", "email", "first_name", "last_name", "phone_number", "password"]
    
    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                msg = 'Access denied: wrong email or password.'
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = 'Both "email" and "password" are required.'
            raise serializers.ValidationError(msg, code='authorization')
        attrs['user'] = user
        return attrs


class PasswordSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    application_name = serializers.CharField(max_length=20)
    site_url = serializers.CharField(max_length=255)
    email_used = serializers.CharField()
    username_used = serializers.CharField(max_length=25)
    password = serializers.CharField()
    
    def create(self, validated_data):
        new_password = Password.objects.create(
            owner = self.context['request'].user,
            application_name = validated_data['application_name'],
            site_url = validated_data['site_url'],
            email_used  = validated_data['email_used'],
            username_used = validated_data['username_used'],
            password = validated_data['password'],
        )
        new_password.save()
        return new_password
    
    class Meta:
        model = Password
        fields = ['id', 'owner', 'application_name', 'site_url', 'email_used', 'username_used', 'password']
        
        
class APIKeySerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    api_key = serializers.UUIDField(read_only=True)

    class Meta:
        model = APIKey
        fields = ['api_key']