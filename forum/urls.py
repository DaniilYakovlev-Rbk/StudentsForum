# forum/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('discussions/', views.discussions, name='discussions'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/update-avatar/', views.update_avatar, name='update_avatar'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('send_message/', views.send_message, name='send_message'),
    path('create_topic/', views.create_topic, name='create_topic'),
    path('clear_register_error/', views.clear_register_error, name='clear_register_error'),
]
