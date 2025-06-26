from django.contrib import admin
from .models import Profile, EmailVerificationCode

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'location', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'phone', 'location')
    list_filter = ('created_at', 'updated_at')

@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('email', 'code', 'created_at', 'is_used')
    search_fields = ('email',)
    list_filter = ('is_used', 'created_at')
