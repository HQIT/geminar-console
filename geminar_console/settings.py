"""
Django settings for geminar-console
用户门户专用配置
"""
from pathlib import Path
from decouple import config
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()

SECRET_KEY = config('SECRET_KEY', default='django-insecure-console-secret-key')
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['*']
ALLOWED_HOSTS += config('ALLOWED_HOSTS', default='').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'console_app',
    'channels',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'geminar_console.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'geminar_console.wsgi.application'
ASGI_APPLICATION = 'geminar_console.asgi.application'

# Database - 共享数据库，只读/受限写入
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': config('DB_NAME', default=BASE_DIR / 'db.sqlite3'),
        'USER': config('DB_USER', default=''),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default=''),
        'PORT': config('DB_PORT', default=''),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'statics'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_URL = config('MEDIA_URL', default='/medias/')
MEDIA_ROOT = config('MEDIA_ROOT', default=BASE_DIR / 'medias')

# OAuth2
OAUTH2_CLIENT_ID = config('OAUTH2_CLIENT_ID', default='')
OAUTH2_CLIENT_SECRET = config('OAUTH2_CLIENT_SECRET', default='')
OAUTH2_AUTHORIZATION_URL = 'https://api.ecnu.edu.cn/oauth2/authorize'
OAUTH2_TOKEN_URL = 'https://api.ecnu.edu.cn/oauth2/token'
OAUTH2_REDIRECT_HOST = config('OAUTH2_REDIRECT_HOST', default='localhost')
OAUTH2_REDIRECT_URI = f'http://{OAUTH2_REDIRECT_HOST}/oauth2/callback'
OAUTH2_USERINFO_URL = 'https://api.ecnu.edu.cn/oauth2/userinfo'
OAUTH2_LOGOUT_URL = 'https://api.ecnu.edu.cn/user/logout'
OAUTH2_USER_PHOTO_URL = 'https://api.ecnu.edu.cn/api/v1/user/photo'
OAUTH2_FACE_COMPARE_URL = 'https://api.ecnu.edu.cn/api/v1/face/compare'

LOGIN_REDIRECT_URL = '/#/welcome'
LOGOUT_REDIRECT_URL = '/login/'

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'PAGE_SIZE_QUERY_PARAM': 'size',
    'MAX_PAGE_SIZE': 100,
}

SESSION_COOKIE_AGE = 3600

CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='').split(',')

# CORS 配置
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='').split(',')
CORS_ALLOW_CREDENTIALS = True

# 是否启用人脸验证（创建讲师时验证上传照片是否为本人）
FACE_VERIFY_ENABLED = config('FACE_VERIFY_ENABLED', default=True, cast=bool)

# RabbitMQ 配置（用于发送任务到 Worker）
RABBITMQ_HOST = config('RABBITMQ_HOST', default='localhost')
RABBITMQ_PORT = config('RABBITMQ_PORT', default=5672, cast=int)
RABBITMQ_USER = config('RABBITMQ_USER', default='guest')
RABBITMQ_PASSWORD = config('RABBITMQ_PASSWORD', default='guest')

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}

