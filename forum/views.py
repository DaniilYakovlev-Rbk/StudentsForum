from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .models import Profile, EmailVerificationCode, Topic
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .telegram_bot import bot
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.template.loader import render_to_string

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
        first_name = request.POST.get('firstName')
        last_name = request.POST.get('lastName')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirmPassword')

        if password != confirm_password:
            messages.error(request, 'Пароли не совпадают')
            return redirect('index')

        if User.objects.filter(username=email).exists():
            messages.error(request, 'Пользователь с таким email уже существует')
            return redirect('index')

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        phone = request.POST.get('phone')
        bio = request.POST.get('bio')

        Profile.objects.create(user=user, phone=phone, bio=bio)

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
        
        messages.success(request, 'Вы успешно зарегистрировались!')
        return redirect('index')

    return redirect('index')

@login_required
def profile(request):
    return render(request, 'forum/profile.html')

def logout_view(request):
    logout(request)
    return redirect('index')

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

def login_view(request):
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'send_code':
                email = data.get('email')
                password = data.get('password')
                
                user = authenticate(request, username=email, password=password)
                if user is not None:
                    code = EmailVerificationCode.create_code(email)
                    send_verification_email(email, code)
                    return JsonResponse({'status': 'success'})
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Неверный email или пароль'
                    })
            
            elif action == 'verify_code':
                email = data.get('email')
                code = data.get('code')
                password = data.get('password')
                
                verification = EmailVerificationCode.objects.filter(
                    email=email,
                    code=code,
                    is_used=False
                ).order_by('-created_at').first()
                
                if verification and verification.is_valid():
                    user = authenticate(request, username=email, password=password)
                    if user is not None:
                        verification.is_used = True
                        verification.save()
                        login(request, user)
                        messages.success(request, 'Вы успешно вошли в систему!')
                        return JsonResponse({'status': 'success', 'message': 'Вы успешно вошли в систему!'})
                
                return JsonResponse({
                    'status': 'error',
                    'message': 'Неверный или устаревший код подтверждения'
                })
            
            elif action == 'resend_code':
                email = data.get('email')
                password = data.get('password')
                
                user = authenticate(request, username=email, password=password)
                if user is not None:
                    code = EmailVerificationCode.create_code(email)
                    send_verification_email(email, code)
                    return JsonResponse({'status': 'success'})
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Неверный email или пароль'
                    })
        
        else:
            messages.error(request, 'Неверный метод входа')
            return redirect('index')

    return redirect('index')

@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        profile = user.profile


        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.save()

        profile.phone = request.POST.get('phone')
        profile.location = request.POST.get('location')
        profile.education = request.POST.get('education')
        profile.interests = request.POST.get('interests')
        profile.bio = request.POST.get('bio')
        profile.save()

        messages.success(request, 'Профиль успешно обновлен!')
        return redirect('profile')

    return redirect('profile')

@login_required
def update_avatar(request):
    if request.method == 'POST' and request.FILES.get('avatar'):
        profile = request.user.profile
        avatar_file = request.FILES['avatar']
        
        if not avatar_file.content_type.startswith('image/'):
            return JsonResponse({
                'status': 'error',
                'message': 'Файл должен быть изображением'
            })
            
        if avatar_file.size > 5 * 1024 * 1024:
            return JsonResponse({
                'status': 'error',
                'message': 'Размер файла не должен превышать 5MB'
            })
            
        try:
            profile.set_avatar(avatar_file)
            
            return JsonResponse({
                'status': 'success',
                'avatar_url': profile.get_avatar_url()
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
            
    return JsonResponse({
        'status': 'error',
        'message': 'Не удалось загрузить аватар'
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