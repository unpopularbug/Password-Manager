from rest_framework.response import Response
from rest_framework import status, viewsets
from django.contrib.auth import login, authenticate, logout
from rest_framework.views import APIView
from rest_framework.decorators import action
from cryptography.fernet import Fernet
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import CustomUser, Password, APIUser
from .serializers import UserSerializer, LoginSerializer, PasswordSerializer, APIUserSerializer
from .permissions import APIKeyPermission

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

    @action(detail=False, methods=['POST'])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            refresh = RefreshToken.for_user(user)
            token = str(refresh.access_token)
            return Response({'token': token, 'user': user.id}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)



class UserLogoutViewset(APIView):
    permission_classes = [APIKeyPermission]
    authentication_classes = [JWTAuthentication]
    
    @action(detail=False, methods=['POST'])
    def post(self, request):
        logout(request)
        return Response({'message': 'User logged out successfully.'}, status=status.HTTP_200_OK)
     
    
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
        encrypted_site_name = fernet.encrypt(validated_data['site_name_or_url'].encode())
        encrypted_email = fernet.encrypt(validated_data['email_used'].encode())
        encrypted_username = fernet.encrypt(validated_data['username_used'].encode())
        encrypted_password = fernet.encrypt(validated_data['password'].encode())
        
        password_instance = serializer.save(
            site_name_or_url=encrypted_site_name,
            email_used=encrypted_email,
            username_used=encrypted_username,
            password=encrypted_password,
        )

        response_serializer = PasswordSerializer(password_instance)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)