import os
from pathlib import Path

# 1. Rutas Base
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Configuración de Seguridad
# ¡CUIDADO! Cambia DEBUG a False solo cuando subas a producción
DEBUG = True

SECRET_KEY = 'django-insecure-4!m$e3i1(-dk91bk2lcgnlbt-a8#rq_b&-i&dyp1!q4cs258n6'

# Si DEBUG es False, debes especificar los dominios aquí
ALLOWED_HOSTS = ['*'] 

# 3. Definición de Aplicaciones
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites', 
    # Tus aplicaciones
    'tikects_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tikects_proyecto.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # Directorio global de templates (opcional)
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'tikects_app.context_processors.agregar_notificaciones',
            ],
        },
    },
]

WSGI_APPLICATION = 'tikects_proyecto.wsgi.application'

# 4. Base de Datos (PostgreSQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'tikectsbd',
        'USER': 'django_user',
        'PASSWORD': 'erick2978',
        'HOST': '127.0.0.1', # localhost
        'PORT': '5432',
    }
}

# 5. Validación de Contraseñas
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 6. Internacionalización (Caracas)
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Caracas'
USE_I18N = True
USE_L10N = True
USE_TZ = True # Recomendado: Django manejará UTC internamente y Caracas en la vista

# 7. Archivos Estáticos y Media
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"

# Directorios donde Django buscará archivos estáticos adicionales
STATICFILES_DIRS = [
    BASE_DIR / "tikects_app/static",
]

# 8. Otros
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SITE_ID = 1 # Necesario porque tienes 'django.contrib.sites' en INSTALLED_APPS

