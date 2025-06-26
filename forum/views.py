from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .models import Topic
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from .telegram_bot import bot
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.template.loader import render_to_string
import requests

def index(request):
    return render(request, 'forum/index.html')

def about(request):
    return render(request, 'forum/about.html')

def discussions(request):
    topic_list = Topic.objects.all().order_by('-created_at')
    
    # Фильтрация по категории
    category = request.GET.get('category')
    if category and category != 'all':
        topic_list = topic_list.filter(category=category)
    
    # Поиск по заголовку и содержанию
    search_query = request.GET.get('search')
    if search_query:
        topic_list = topic_list.filter(
            Q(title__icontains=search_query) | 
            Q(content__icontains=search_query)
        )
    
    # Пагинация
    paginator = Paginator(topic_list, 10)  # 10 тем на страницу
    page = request.GET.get('page')
    
    try:
        topics = paginator.page(page)
    except PageNotAnInteger:
        topics = paginator.page(1)
    except EmptyPage:
        topics = paginator.page(paginator.num_pages)
    
    return render(request, 'forum/discussions.html', {'topics': topics})

def register(request):
    if request.method == 'POST':
        data = {
            "email": request.POST.get('email'),
            "username": request.POST.get('email'),
            "password": request.POST.get('password'),
            "confirm_password": request.POST.get('confirmPassword'),
            "first_name": request.POST.get('firstName'),
            "last_name": request.POST.get('lastName'),
            "phone": request.POST.get('phone', ''),
            "bio": request.POST.get('bio', ''),
        }
        # Проверяем, есть ли пользователь с таким email в Django
        if User.objects.filter(username=data["username"]).exists():
            error_message = "Пользователь с таким email уже существует."
            request.session['register_error'] = error_message
            return redirect('index')
        # Проверяем совпадение паролей до запроса к API
        if data["password"] != data["confirm_password"]:
            request.session['register_error'] = "Пароли не совпадают"
            return redirect('index')
        response = requests.post('http://localhost:8001/api/register/', json=data)
        if response.status_code == 201:
            # После успешной регистрации сразу логиним пользователя
            login_response = requests.post('http://localhost:8001/api/token/', json={
                "username": data["email"],
                "password": data["password"]
            })
            if login_response.status_code == 200:
                try:
                    tokens = login_response.json()
                except Exception:
                    request.session['register_error'] = "Ошибка авторизации после регистрации. Попробуйте войти вручную."
                    return redirect('index')
                request.session['access'] = tokens['access']
                request.session['refresh'] = tokens['refresh']
                headers = {'Authorization': f'Bearer {tokens["access"]}'}
                profile_response = requests.get('http://localhost:8001/api/profile/', headers=headers)
                if profile_response.status_code == 200:
                    try:
                        profile_data = profile_response.json()[0]
                    except Exception:
                        request.session['register_error'] = "Ошибка получения профиля после регистрации"
                        return redirect('index')
                    from django.db import IntegrityError
                    try:
                        user, created = User.objects.get_or_create(
                            username=profile_data['user']['username'],
                            defaults={
                                'email': profile_data['user']['email'],
                                'first_name': profile_data['user']['first_name'],
                                'last_name': profile_data['user']['last_name'],
                            }
                        )
                        if not created:
                            user.email = profile_data['user']['email']
                            user.first_name = profile_data['user']['first_name']
                            user.last_name = profile_data['user']['last_name']
                            user.save()
                    except IntegrityError:
                        error_message = "Пользователь с таким email уже существует."
                        request.session['register_error'] = error_message
                        return redirect('index')
                    login(request, user)
                    request.session['profile_data'] = profile_data
                    messages.success(request, "Регистрация успешна! Вы вошли в систему.")
                    return redirect('profile')
                else:
                    request.session['register_error'] = "Ошибка получения профиля после регистрации"
            else:
                request.session['register_error'] = "Ошибка автоматического входа после регистрации"
            return redirect('index')
        else:
            try:
                errors = response.json()
            except Exception:
                errors = response.text
            # Преобразуем ошибки в строку для отображения
            error_message = None
            if isinstance(errors, dict):
                # Если есть ключ error_fields и там про пароли
                if 'error_fields' in errors and 'пароли не совпадают' in str(errors['error_fields']).lower():
                    error_message = "Пароли не совпадают"
                elif 'username' in errors and 'уже существует' in str(errors['username']).lower():
                    error_message = "Пользователь с таким email уже существует."
                else:
                    error_message = '\n'.join([f"{k}: {v}" for k, v in errors.items()])
            else:
                error_message = str(errors)
            request.session['register_error'] = error_message
    return redirect('index')

def login_view(request):
    if request.method == 'POST':
        data = {
            "email": request.POST.get('email'),
            "password": request.POST.get('password'),
        }
        response = requests.post('http://localhost:8001/api/token/', json={
            "username": data["email"],
            "password": data["password"]
        })
        if response.status_code == 200:
            tokens = response.json()
            request.session['access'] = tokens['access']
            request.session['refresh'] = tokens['refresh']
            
            # Получаем данные пользователя для аутентификации в Django
            headers = {'Authorization': f'Bearer {tokens["access"]}'}
            profile_response = requests.get('http://localhost:8001/api/profile/', headers=headers)
            
            if profile_response.status_code == 200:
                profile_data = profile_response.json()[0]
                # Создаем или получаем пользователя в Django
                user, created = User.objects.get_or_create(
                    username=profile_data['user']['username'],
                    defaults={
                        'email': profile_data['user']['email'],
                        'first_name': profile_data['user']['first_name'],
                        'last_name': profile_data['user']['last_name'],
                    }
                )
                
                # Если пользователь уже существует, обновляем его данные
                if not created:
                    user.email = profile_data['user']['email']
                    user.first_name = profile_data['user']['first_name']
                    user.last_name = profile_data['user']['last_name']
                    user.save()
                
                # Аутентифицируем пользователя в Django
                login(request, user)
                
                # Сохраняем данные профиля в сессии для использования в шаблонах
                request.session['profile_data'] = profile_data
                
                messages.success(request, "Вы успешно вошли в систему")
                return redirect('profile')
            else:
                messages.error(request, "Ошибка получения данных профиля")
        else:
            messages.error(request, "Неверный email или пароль")
    return redirect('index')

def logout_view(request):
    # Выходим из Django
    logout(request)
    # Очищаем все данные сессии
    request.session.flush()
    messages.success(request, "Вы вышли из аккаунта.")
    return redirect('index')

def profile(request):
    # Проверяем, аутентифицирован ли пользователь в Django
    if not request.user.is_authenticated:
        return redirect('index')
    
    # Получаем данные профиля из сессии или из API
    profile_data = request.session.get('profile_data')
    
    if not profile_data:
        # Если данных нет в сессии, получаем их из API
        access_token = request.session.get('access')
        if not access_token:
            return redirect('index')
        
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get('http://localhost:8001/api/profile/', headers=headers)
        if response.status_code == 200:
            profile_data = response.json()[0]
            request.session['profile_data'] = profile_data
        else:
            messages.error(request, "Ошибка доступа к профилю")
            return redirect('index')
    
    return render(request, 'forum/profile.html', {'profile': profile_data})

def update_profile(request):
    access_token = request.session.get('access')
    if not access_token:
        return redirect('login')
    if request.method == 'POST':
        headers = {'Authorization': f'Bearer {access_token}'}
        data = {
            "first_name": request.POST.get('first_name'),
            "last_name": request.POST.get('last_name'),
            "phone": request.POST.get('phone'),
            "location": request.POST.get('location'),
            "education": request.POST.get('education'),
            "interests": request.POST.get('interests'),
            "bio": request.POST.get('bio'),
        }
        response = requests.put('http://localhost:8001/api/profile/update_profile/', json=data, headers=headers)
        if response.status_code == 200:
            messages.success(request, "Профиль успешно обновлен!")
        else:
            messages.error(request, "Ошибка при обновлении профиля")
    return redirect('profile')

def update_avatar(request):
    access_token = request.session.get('access')
    if not access_token:
        return redirect('login')
    if request.method == 'POST' and request.FILES.get('avatar'):
        headers = {'Authorization': f'Bearer {access_token}'}
        files = {'avatar': request.FILES['avatar']}
        response = requests.post('http://localhost:8001/api/profile/update_avatar/', files=files, headers=headers)
        if response.status_code == 200:
            messages.success(request, "Аватар успешно обновлен!")
        else:
            messages.error(request, "Ошибка при обновлении аватара")
    return redirect('profile')

@login_required
@require_http_methods(["POST"])
def create_topic(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'error',
            'message': 'Для создания темы необходимо войти в систему'
        }, status=403)

    try:
        title = request.POST.get('title')
        category = request.POST.get('category')
        content = request.POST.get('content')
        
        if not all([title, category, content]):
            return JsonResponse({
                'status': 'error',
                'message': 'Пожалуйста, заполните все поля'
            })
        
        valid_categories = dict(Topic.CATEGORY_CHOICES)
        if category not in valid_categories:
            return JsonResponse({
                'status': 'error',
                'message': f'Недопустимая категория. Допустимые категории: {", ".join(valid_categories.keys())}'
            })
        
        topic = Topic.objects.create(
            title=title,
            category=category,
            content=content,
            author=request.user
        )
        
        # Получаем все темы для первой страницы
        topics = Topic.objects.all().order_by('-created_at')
        paginator = Paginator(topics, 10)  
        first_page = paginator.page(1)
        
        topics_data = []
        for topic in first_page:
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
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "topics",
            {
                "type": "topics_update",
                "data": {
                    "topics": topics_data,  
                    "pagination": {
                        "has_previous": first_page.has_previous(),
                        "has_next": first_page.has_next(),
                        "current_page": first_page.number,
                        "total_pages": paginator.num_pages,
                        "page_range": list(paginator.page_range)
                    }
                }
            }
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Тема успешно создана',
            'topic': topics_data[0]  
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка при создании темы: {str(e)}'
        })

@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not request.user.check_password(current_password):
            messages.error(request, 'Неверный текущий пароль')
            return redirect('profile')

        if new_password != confirm_password:
            messages.error(request, 'Пароли не совпадают')
            return redirect('profile')

        request.user.set_password(new_password)
        request.user.save()
        
        user = authenticate(username=request.user.username, password=new_password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Пароль успешно изменен!')
        
        return redirect('profile')

    return redirect('profile')

@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    try:
        data = json.loads(request.body)
        
        message = bot.format_contact_message(data)
        
        
        CHAT_ID = "829407178" 
        result = bot.send_message(CHAT_ID, message)
        
        if result and result.get('ok'):
            return JsonResponse({
                'status': 'success',
                'message': 'Message sent successfully'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to send message'
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'Error processing request'
        }, status=500)

@require_POST
def clear_register_error(request):
    if 'register_error' in request.session:
        del request.session['register_error']
    return JsonResponse({'status': 'ok'})