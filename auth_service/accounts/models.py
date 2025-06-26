from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random
import base64

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    avatar_data = models.BinaryField(null=True, blank=True, editable=True) 
    avatar_content_type = models.CharField(max_length=255, null=True, blank=True)  
    location = models.CharField(max_length=100, blank=True)
    education = models.CharField(max_length=200, blank=True)
    interests = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

    def set_avatar(self, file):
        if file:
            self.avatar_content_type = file.content_type
            self.avatar_data = file.read()
            self.save()

    def get_avatar_url(self):
        if self.avatar_data:
            return f"data:{self.avatar_content_type};base64,{base64.b64encode(self.avatar_data).decode('utf-8')}"
        return None

class EmailVerificationCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    email = models.EmailField()  
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"Verification code for {self.email}"

    @classmethod
    def generate_code(cls):
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])

    @classmethod
    def create_code(cls, email):
        cls.objects.filter(email=email).update(is_used=True)
        code = cls.generate_code()  
        verification = cls.objects.create(
            email=email,
            code=code
        )
        return code

    def is_valid(self):
        if self.is_used:
            return False
        time_diff = timezone.now() - self.created_at
        return time_diff.total_seconds() < 600
