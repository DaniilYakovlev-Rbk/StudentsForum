from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from .models import Profile, EmailVerificationCode
from .serializers import (
    UserSerializer, ProfileSerializer, UserRegistrationSerializer,
    EmailVerificationSerializer, ProfileUpdateSerializer
)

# Create your views here.

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_request(request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    user = authenticate(username=email, password=password)
    if user is not None:
        code = EmailVerificationCode.create_code(email)
        send_verification_email(email, code)
        return Response({'status': 'success'})
    return Response({
        'status': 'error',
        'message': 'Неверный email или пароль'
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_code(request):
    email = request.data.get('email')
    code = request.data.get('code')
    password = request.data.get('password')
    
    verification = EmailVerificationCode.objects.filter(
        email=email,
        code=code,
        is_used=False
    ).order_by('-created_at').first()
    
    if verification and verification.is_valid():
        user = authenticate(username=email, password=password)
        if user is not None:
            verification.is_used = True
            verification.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            })
    
    return Response({
        'status': 'error',
        'message': 'Неверный или устаревший код подтверждения'
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def resend_code(request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    user = authenticate(username=email, password=password)
    if user is not None:
        code = EmailVerificationCode.create_code(email)
        send_verification_email(email, code)
        return Response({'status': 'success'})
    return Response({
        'status': 'error',
        'message': 'Неверный email или пароль'
    }, status=status.HTTP_400_BAD_REQUEST)

class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)

    def get_object(self):
        return self.request.user.profile

    @action(detail=False, methods=['put'], serializer_class=ProfileUpdateSerializer)
    def update_profile(self, request):
        profile = self.get_object()
        serializer = ProfileUpdateSerializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(ProfileSerializer(profile).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def update_avatar(self, request):
        profile = self.get_object()
        if 'avatar' not in request.FILES:
            return Response({
                'status': 'error',
                'message': 'Файл не предоставлен'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        avatar_file = request.FILES['avatar']
        if not avatar_file.content_type.startswith('image/'):
            return Response({
                'status': 'error',
                'message': 'Файл должен быть изображением'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if avatar_file.size > 5 * 1024 * 1024:
            return Response({
                'status': 'error',
                'message': 'Размер файла не должен превышать 5MB'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            profile.set_avatar(avatar_file)
            return Response({
                'status': 'success',
                'avatar_url': profile.get_avatar_url()
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

def send_verification_email(email, code):
    subject = 'Код подтверждения для входа на StudForum'
    message = f'''
    Здравствуйте!
    
    Ваш код подтверждения для входа на StudForum: {code}
    
    Код действителен в течение 10 минут.
    
    Если вы не запрашивали этот код, просто проигнорируйте это письмо.
    
    С уважением,
    Команда StudForum
    '''
    send_mail(
        subject,
        message,
        None,
        [email],
        fail_silently=False,
    )
