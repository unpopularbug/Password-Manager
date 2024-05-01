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
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.shortcuts import get_object_or_404


from .models import CustomUser, Password, ApiUser, VerificationCode, PasswordResetCode, QuickTip
from .serializers import UserSerializer, LoginSerializer, PasswordSerializer, APIUserSerializer, PasswordResetSerializer, PasswordConfirmSerializer, ResendCodeSerializer
from .permissions import APIKeyPermission
from .filters import MyDjangoFilter
from django.conf import settings


#pylint: disable=no-member
def send_verification_code(request, user):
    VerificationCode.objects.filter(user=user).delete()
    
    verification_code = ''.join(random.choices(string.digits, k=6))
    
    VerificationCode.objects.create(user=user, code=verification_code)
    
    subject = "Account Verification Code"
    sender_name = 'The Two Devs Team'
    sender_email = settings.EMAIL_HOST_USER
    recipient_email = user.email

    html_message = render_to_string('verification_email.html', {
        'verification_code': verification_code,
        'sender_name': sender_name,
    })

    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject,
            plain_message,
            f"{sender_name} <{sender_email}>",
            [recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending email: {e}")
    

class ResendVerificationCode(APIView):
    serializer_class = ResendCodeSerializer
    
    def post(self, request):
        email = request.data.get('email', None)
        
        if email:
            existing_user = CustomUser.objects.filter(email=email).first()
            if existing_user:
                serializer = self.serializer_class(existing_user)
                send_verification_code(request=request, user=existing_user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({'detail': 'User with this email does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
                

class UserViewset(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [APIKeyPermission]
    filter_backends = [MyDjangoFilter]
    search_fields = ['email', 'first_name', 'last_name']
    
    @action(methods=['POST'], detail=False)
    def register(self, request):
        email = request.data.get('email', None)
        if email:
            existing_user = CustomUser.objects.filter(email=email).exists()
            if existing_user:
                return Response({'detail': 'This email is already in use.'}, status=status.HTTP_400_BAD_REQUEST)
            
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        user = serializer.instance
        
        send_verification_code(request=request, user=user)
        
        user_id = user.id
        response_data = {'user_id': user_id}
        headers = self.get_success_headers(response_data)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(methods=['POST'], detail=False)
    def confirm_code(self, request, user_id):
        code = request.data.get('verification_code')
        user = get_object_or_404(CustomUser, id=user_id)
        
        verification_code = VerificationCode.objects.filter(user=user).first()
        
        if verification_code and verification_code.code == code:
            user.is_verified = True
            user.save()
            verification_code.delete()
            return Response({'message': 'Email verified & account activated.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid verification code.'}, status=status.HTTP_400_BAD_REQUEST)
        

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
            if user.is_verified == True:
                login(request, user)
                refresh = RefreshToken.for_user(user)
                token = str(refresh.access_token)
                return Response({'token': token, 'user': user.id}, status=status.HTTP_200_OK)
            elif user.is_verified == False:
                return Response({'error': 'Your account needs to be verified to proceed.'}, status=status.HTTP_400_BAD_REQUEST)
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
    authentication_classes = [JWTAuthentication]
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
        queryset = Password.objects.filter(owner=self.request.user)
        
        for obj in queryset:
            fernet_key = obj.decryption_key
            if fernet_key:
                fernet = Fernet(fernet_key)
                decrypted_application_name = fernet.decrypt(obj.application_name.encode()).decode()
                obj.application_name = decrypted_application_name
        
        return queryset
    

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

        subject = "Password Reset Code"
        sender_name = 'The Two Devs Team'
        sender_email = settings.EMAIL_HOST_USER
        recipient_email = user.email

        html_message = render_to_string('reset_code_email.html', {
            'verification_code': verification_code,
            'sender_name': sender_name,
        })

        plain_message = strip_tags(html_message)

        try:
            send_mail(
                subject,
                plain_message,
                f"{sender_name} <{sender_email}>",
                [recipient_email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error sending email: {e}")

        return Response({"message": "A reset code has been sent to your email."}, status=status.HTTP_200_OK)
    
    
class PasswordConfirmView(APIView):
    serializer_class = PasswordConfirmSerializer
    permission_classes = [APIKeyPermission]
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        new_password = serializer.validated_data['new_password']
        verification_code = serializer.validated_data['verification_code']
        

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
        reset_code.delete()

        return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)
    
    
class QuickTipViewset(APIView):
    permission_classes = [APIKeyPermission]
    
    def get(self, request):
        queryset = QuickTip.objects.all()
        return Response(data=queryset.values(), status=200)
    
    # Task: Schedule quick tips and show each for three days.