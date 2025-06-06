from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/topics/$', consumers.TopicConsumer.as_asgi()),
] 