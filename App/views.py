from rest_framework.response import Response
from rest_framework import status, viewsets
from django.contrib.auth import login
from rest_framework.views import APIView
from rest_framework.decorators import action
from cryptography.fernet import Fernet

from .models import CustomUser, Password, APIUser
from .serializers import UserSerializer, LoginSerializer, PasswordSerializer, APIUserSerializer
from mylib.permissions import APIKeyPermission

#pylint: disable=no-member
class UserViewset(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [APIKeyPermission]
    
    @action(methods=['POST'], detail=False)
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        

class APIUserViewset(viewsets.ModelViewSet):
    queryset = APIUser.objects.all()
    serializer_class = APIUserSerializer
    permission_classes = [APIKeyPermission]
    
    @action(methods=['POST'], detail=False)
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
class LoginViewset(APIView):
    serializer_class = LoginSerializer
    permission_classes = [APIKeyPermission]

    @action(methods=['POST'], detail=False)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return Response(status=status.HTTP_200_OK)
    
    
class PasswordViewset(viewsets.ModelViewSet):
    queryset = Password.objects.all()
    serializer_class = PasswordSerializer
    permission_classes = [APIKeyPermission]
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        
        key = Fernet.generate_key()
        fernet = Fernet(key)
        encrypted_email = fernet.encrypt(validated_data['email_used'].encode())
        encrypted_username = fernet.encrypt(validated_data['username_used'].encode())
        encrypted_password = fernet.encrypt(validated_data['password'].encode())
        
        password_instance = serializer.save(
            email_used=encrypted_email,
            username_used=encrypted_username,
            password=encrypted_password,
        )

        response_serializer = PasswordSerializer(password_instance)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)