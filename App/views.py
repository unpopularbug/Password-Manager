import random
import string
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.contrib.auth import login, authenticate, logout
from rest_framework.views import APIView
from rest_framework.decorators import action
from cryptography.fernet import Fernet
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.mail import send_mail


from .models import CustomUser, Password, ApiUser, PasswordResetCode
from .serializers import UserSerializer, LoginSerializer, PasswordSerializer, APIUserSerializer, PasswordResetSerializer, PasswordConfirmSerializer
from .permissions import APIKeyPermission
from .filters import MyDjangoFilter
from django.conf import settings

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
        self._encrypt_password(serializer.instance)

    def perform_update(self, serializer):
        instance = serializer.instance
        self._encrypt_password(instance, serializer.validated_data)
        super().perform_update(serializer)

    def _encrypt_password(self, instance, data=None):
        fernet_key = instance.decryption_key
        encrypted_data = self._encrypt_data(data or instance.__dict__, fernet_key)
        for key, value in encrypted_data.items():
            setattr(instance, key, value)
        instance.save()

    def _encrypt_data(self, data, fernet_key):
        encrypted_data = {}
        fernet = Fernet(fernet_key)
        for key, value in data.items():
            if isinstance(value, str):
                encrypted_value = fernet.encrypt(value.encode()).decode()
                encrypted_data[key] = encrypted_value
        return encrypted_data

    def _decrypt_data(self, instance, fernet_key):
        fernet = Fernet(fernet_key)
        decrypted_data = {}
        for key, value in instance.__dict__.items():
            if isinstance(value, str):
                decrypted_value = fernet.decrypt(value.encode()).decode()
                decrypted_data[key] = decrypted_value
        return decrypted_data

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.owner != request.user:
            return Response({"error": "You are not authorized to view this password."}, status=status.HTTP_403_FORBIDDEN)

        fernet_key = instance.decryption_key
        if not fernet_key:
            return Response({"error": "Decryption key not found."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        decrypted_data = self._decrypt_data(instance, fernet_key)
        return Response(decrypted_data)
    
    def get_queryset(self):
        return Password.objects.filter(owner=self.request.user)
    

class PasswordResetView(APIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [APIKeyPermission]
    
    def post(self, request):
        email = request.data.get('email')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({"error": "A user with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)

        verification_code = ''.join(random.choices(string.digits, k=6))
        
        PasswordResetCode.objects.create(user=user, code=verification_code)

        send_mail(
            "Password Reset Verification Code",
            f"Dear User,\n\nYour password reset verification code is: {verification_code}.\n\nThis code is valid for 5 minutes.\n\nThank you!",
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        return Response({"message": "A verification code has been sent to your email."}, status=status.HTTP_200_OK)
    
    
class PasswordConfirmView(APIView):
    serializer_class = PasswordConfirmSerializer
    permission_classes = [APIKeyPermission]
    
    def post(self, request):
        email = request.data.get('email')
        verification_code = request.data.get('verification_code')
        new_password = request.data.get('new_password')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({"error": "A user with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)

        # Validate verification code
        try:
            reset_code = PasswordResetCode.objects.get(user__email=email, code=verification_code)
        except PasswordResetCode.DoesNotExist:
            return Response({"error": "Invalid verification code."}, status=status.HTTP_400_BAD_REQUEST)

        user = reset_code.user
        user.set_password(new_password)
        user.save()

        return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)