"""
============================================================
⚙️ SIGEM - Configurações do Django
Sistema de Gestão de Missões - CBMGO
============================================================
"""

import os
from pathlib import Path

# Tentar importar dj_database_url (usado no Render)
try:
    import dj_database_url
except ImportError:
    dj_database_url = None

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# 🔐 SEGURANÇA
# ============================================================
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-key-mude-em-producao')
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')

# Hosts permitidos
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Adicionar host do Render se existir
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Adicionar hosts extras se configurados
EXTRA_HOSTS = os.environ.get('ALLOWED_HOSTS', '')
if EXTRA_HOSTS:
    ALLOWED_HOSTS.extend(EXTRA_HOSTS.split(','))

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
    'whitenoise.middleware.WhiteNoiseMiddleware',  # WhiteNoise para arquivos estáticos
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
# 🗄️ BANCO DE DADOS
# ============================================================
# Verificar se existe DATABASE_URL (Render/Neon)
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL and dj_database_url:
    # Produção: usar DATABASE_URL do Neon
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,
        )
    }
else:
    # Local: usar configurações do .env ou padrão
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'sigem'),
            'USER': os.environ.get('DB_USER', 'sigem_user'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'sigem123'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
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

# WhiteNoise para servir arquivos estáticos em produção
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

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

# ============================================================
# 🔒 SEGURANÇA EM PRODUÇÃO
# ============================================================
if not DEBUG:
    # HTTPS
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    
    # CSRF
    CSRF_TRUSTED_ORIGINS = []
    if RENDER_EXTERNAL_HOSTNAME:
        CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')

# ============================================================
# 🔗 INTEGRAÇÃO COM SICAD
# ============================================================
# URL do filesystem do SICAD para fotos de oficiais
# Formato: https://sicad.example.com/fotos/{id}/{hash}
SICAD_FILESYSTEM_URL = os.environ.get('SICAD_FILESYSTEM_URL', '')
