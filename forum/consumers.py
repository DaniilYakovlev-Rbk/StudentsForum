import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Topic
from django.core.paginator import Paginator
from django.db.models import Q

class TopicConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("topics", self.channel_name)
        await self.accept()
        
        # Отправляем начальные данные при подключении
        topics_data = await self.get_topics_data()
        await self.send(json.dumps({
            'type': 'topics_update',
            'data': topics_data
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("topics", self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get('action') == 'get_topics':
                topics_data = await self.get_topics_data(
                    page=int(data.get('page', 1)),
                    category=data.get('category'),
                    search=data.get('search')
                )
                await self.send(json.dumps({
                    'type': 'topics_update',
                    'data': topics_data
                }))
        except Exception as e:
            await self.send(json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def topics_update(self, event):
        # Отправка обновления клиенту
        await self.send(text_data=json.dumps(event))

    async def new_topic_notification(self, event):
        # Отправка уведомления о новой теме
        await self.send(text_data=json.dumps({
            'type': 'new_topic',
            'data': event['data']
        }))

    @database_sync_to_async
    def get_topics_data(self, page=1, category=None, search=None):
        # Получаем все темы
        topics = Topic.objects.all().order_by('-created_at')
        
        if category and category != 'all':
            topics = topics.filter(category=category)
            
        if search:
            topics = topics.filter(
                Q(title__icontains=search) | 
                Q(content__icontains=search)
            )
        
        paginator = Paginator(topics, 10)  
        
        try:
            topics_page = paginator.page(page)
        except:
            topics_page = paginator.page(1)

        topics_data = []
        for topic in topics_page:
            topics_data.append({
                'id': topic.id,
                'title': topic.title,
                'content': topic.content,
                'category': topic.category,
                'category_display': topic.get_category_display(),
                'author': topic.author.username,
                'created_at': topic.created_at.strftime('%d %B %Y'),
                'views': topic.views
            })

        # Возвращаем данные тем и информацию о пагинации
        return {
            'topics': topics_data,
            'pagination': {
                'has_previous': topics_page.has_previous(),
                'has_next': topics_page.has_next(),
                'current_page': topics_page.number,
                'total_pages': paginator.num_pages,
                'page_range': list(paginator.page_range)
            }
        } 