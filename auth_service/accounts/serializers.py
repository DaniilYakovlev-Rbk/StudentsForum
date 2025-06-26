from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, EmailVerificationCode

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        read_only_fields = ('id',)

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ('user', 'phone', 'bio', 'location', 'education', 
                 'interests', 'created_at', 'updated_at', 'avatar_url')
        read_only_fields = ('created_at', 'updated_at')

    def get_avatar_url(self, obj):
        return obj.get_avatar_url()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'confirm_password',
                  'first_name', 'last_name', 'phone', 'bio')

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Пароли не совпадают")
        return data

    def create(self, validated_data):
        phone = validated_data.pop('phone', '')
        bio = validated_data.pop('bio', '')
        validated_data.pop('confirm_password')
        email = validated_data['email']
        user = User.objects.create_user(
            username=email,  # username всегда равен email
            email=email,
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        Profile.objects.create(user=user, phone=phone, bio=bio)
        return user

class EmailVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailVerificationCode
        fields = ('email', 'code')

class ProfileUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')

    class Meta:
        model = Profile
        fields = ('first_name', 'last_name', 'phone', 'location',
                 'education', 'interests', 'bio')

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user

        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance 