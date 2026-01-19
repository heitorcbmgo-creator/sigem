"""
============================================================
⚙️ SIGEM - Configurações do Django
Sistema de Gestão de Missões - CBMGO
============================================================
"""

from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# 🔐 SEGURANÇA
# ============================================================
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# ============================================================
# 📦 APLICAÇÕES INSTALADAS
# ============================================================
INSTALLED_APPS = [
    # Django padrão
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Apps de terceiros
    'django_htmx',
    
    # Apps do SIGEM
    'missoes',
]

# ============================================================
# 🔧 MIDDLEWARE
# ============================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',  # HTMX
]

ROOT_URLCONF = 'core.urls'

# ============================================================
# 📄 TEMPLATES
# ============================================================
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

WSGI_APPLICATION = 'core.wsgi.application'

# ============================================================
# 🗄️ BANCO DE DADOS - PostgreSQL
# ============================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='sigem'),
        'USER': config('DB_USER', default='sigem_user'),
        'PASSWORD': config('DB_PASSWORD', default='sigem123'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# ============================================================
# 🔑 VALIDAÇÃO DE SENHA
# ============================================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ============================================================
# 👤 MODELO DE USUÁRIO CUSTOMIZADO
# ============================================================
AUTH_USER_MODEL = 'missoes.Usuario'

# ============================================================
# 🌍 INTERNACIONALIZAÇÃO
# ============================================================
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# ============================================================
# 📁 ARQUIVOS ESTÁTICOS (CSS, JS, Imagens)
# ============================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ============================================================
# 📷 ARQUIVOS DE MÍDIA (Uploads)
# ============================================================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ============================================================
# 🔗 CONFIGURAÇÕES DE LOGIN
# ============================================================
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# ============================================================
# 🆔 TIPO DE CAMPO PRIMÁRIO PADRÃO
# ============================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================
# 💬 MENSAGENS (para feedback ao usuário)
# ============================================================
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}
