from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random
import base64

class Topic(models.Model):
    CATEGORY_CHOICES = [
        ('study', 'Учеба'),
        ('career', 'Карьера'),
        ('campus', 'Кампус'),
        ('entertainment', 'Развлечения'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.IntegerField(default=0)
    
    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']
