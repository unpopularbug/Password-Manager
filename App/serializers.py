from rest_framework import serializers
from django.contrib.auth import authenticate

from .models import CustomUser, Password

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
        fields = [ "id", "email", "password"]

 
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
    owner = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    site_name_or_url = serializers.CharField(max_length=20)
    email_used = serializers.CharField()
    username_used = serializers.CharField(max_length=25)
    password = serializers.CharField()
    
    def create(self, validated_data):
        new_password = Password.objects.create(
            owner = self.context['request'].user,
            site_name_or_url = validated_data['site_name_or_url'],
            email_used  = validated_data['email_used'],
            username_used = validated_data['username_used'],
            password = validated_data['password'],
        )
        new_password.save()
        return new_password
    
    class Meta:
        model = Password
        fields = ['owner', 'site_name_or_url', 'email_used', 'username_used', 'password']