from rest_framework import serializers
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


class PasswordSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    application_name = serializers.CharField(max_length=20)
    site_url = serializers.CharField()
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
        fields = ['owner', 'application_name', 'site_url', 'email_used', 'username_used', 'password']