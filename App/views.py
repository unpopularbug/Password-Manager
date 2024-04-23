from rest_framework.response import Response
from rest_framework import status, viewsets
from django.contrib.auth import login, authenticate, logout
from rest_framework.views import APIView
from rest_framework.decorators import action
from cryptography.fernet import Fernet
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import CustomUser, Password, ApiUser
from .serializers import UserSerializer, LoginSerializer, PasswordSerializer, APIUserSerializer
from .permissions import APIKeyPermission
from .filters import MyDjangoFilter

#pylint: disable=no-member
class UserViewset(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [APIKeyPermission]
    filter_backends = [MyDjangoFilter]
    search_fields = ['email', 'first_name', 'last_name']
    
    @action(methods=['POST'], detail=False)
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        

class APIUserViewset(viewsets.ModelViewSet):
    queryset = ApiUser.objects.all()
    serializer_class = APIUserSerializer
    permission_classes = [APIKeyPermission]
    filter_backends = [MyDjangoFilter]
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    
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



class LogoutViewset(APIView):
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
    filter_backends = [MyDjangoFilter]
    search_fields = ['application_name', 'site_url', 'email_used', 'username_used']

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        
        fernet_key = Fernet.generate_key()
        
        self.request.user.private_key = fernet_key
        self.request.user.save()
            
        encrypted_data = {}
        for key, value in validated_data.items():
            fernet = Fernet(fernet_key)
            encrypted_value = fernet.encrypt(value.encode())
            encrypted_data[key] = encrypted_value
        
        password_instance = serializer.save(**encrypted_data)

        response_serializer = PasswordSerializer(password_instance)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    
    def decrypt_data(self, encrypted_data, fernet_key):
        decrypted_data = {}
        fernet = Fernet(fernet_key)
        for key, value in encrypted_data.items():
            decrypted_data[key] = fernet.decrypt(value).decode()
        return decrypted_data
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.owner != request.user:
            return Response({"error": "You are not authorized to view this password."}, status=status.HTTP_403_FORBIDDEN)

        user_fernet_key = request.user.private_key

        decrypted_data = {}
        fernet = Fernet(user_fernet_key)

        decrypted_data['application_name'] = fernet.decrypt(instance.application_name.encode()).decode()
        decrypted_data['site_url'] = fernet.decrypt(instance.site_url.encode()).decode()
        decrypted_data['email_used'] = fernet.decrypt(instance.email_used.encode()).decode()
        decrypted_data['username_used'] = fernet.decrypt(instance.username_used.encode()).decode()
        decrypted_data['password'] = fernet.decrypt(instance.password.encode()).decode()

        serializer = self.get_serializer(decrypted_data)
        return Response(serializer.data)
    
    
    def get_queryset(self):
        return Password.objects.filter(owner=self.request.user)