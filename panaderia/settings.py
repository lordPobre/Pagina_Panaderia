import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY')

DEBUG = os.getenv('DEBUG') == 'True'

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = [
    'https://*.ngrok-free.app',
    'https://85aa-179-60-77-168.ngrok-free.app' # O la URL específica que te dio el error
]

INSTALLED_APPS = [
    'jazzmin',
    'core.apps.CoreConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
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

ROOT_URLCONF = 'panaderia.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'panaderia.wsgi.application'

JAZZMIN_SETTINGS = {
    # Textos principales
    "site_title": "Gestión Panadería",
    "site_header": "Panel de Administración",
    "site_brand": "La Panadería", # Aquí puedes poner el nombre real
    "welcome_sign": "Bienvenido al sistema de gestión",
    "copyright": "Perseus Technology",
    
    # Buscador superior (Busca en órdenes y productos a la vez)
    "search_model": ["core.Orden", "core.Producto"],

    # --- MENÚ LATERAL MEJORADO ---
    "show_sidebar": True,
    "navigation_expanded": True,
    
    # Iconos para cada sección (usando FontAwesome 5)
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user-shield",
        "auth.Group": "fas fa-users",
        "core.Producto": "fas fa-bread-slice",     # Icono de pan
        "core.Orden": "fas fa-shopping-basket",    # Icono de canasta de compra
    },
    
    # Icono por defecto si olvidas ponerle a algún modelo nuevo
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    # --- ORDENAMIENTO PERSONALIZADO ---
    # Aquí forzamos a que las cosas aparezcan en el orden que más usará el dueño
    "order_with_respect_to": ["core.Orden", "core.Producto", "auth"],

    # Ocultar aplicaciones que el dueño no necesita ver (como menús internos de Django)
    "hide_apps": [], 
    "hide_models": ["core.Orden"],

    # --- BOTONES RÁPIDOS EN LA BARRA SUPERIOR ---
    "topmenu_links": [
        {"name": "Ver Tienda", "url": "/", "new_window": True}, # Para ir a la página web real
        {"model": "core.Orden"}, # Acceso directo a las ventas
    ],
    "topmenu_links": [
    {"name": "Pendientes", "url": "admin:core_ordenactiva_changelist"},
    {"name": "Historial", "url": "admin:core_ordenhistorial_changelist"},
    ],
}
JAZZMIN_UI_TWEAKS = {
    # 'lumen' o 'flatly' son los temas que más se parecen a tu imagen (limpios y planos)
    "theme": "lumen", 
    "dark_mode_theme": None,
    
    # El contraste exacto de tu imagen:
    "sidebar": "sidebar-dark-primary",  # Barra lateral oscura/negra
    "navbar": "navbar-white navbar-light", # Barra superior blanca y limpia
    "brand_colour": "navbar-white",     # Fondo del logo en blanco
    
    "accent": "accent-primary",         
    
    # Comportamiento moderno
    "sidebar_fixed": True,              # La barra lateral se queda quieta al bajar
    "sidebar_nav_flat_style": True,     # Quita bordes 3D antiguos
    "sidebar_nav_child_indent": True,   # Submenús ordenados
    
    # Botones estilo minimalista
    "button_classes": {
        "primary": "btn-dark",          # Botones principales oscuros como en la imagen
        "secondary": "btn-outline-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    },
    "actions_sticky_top": True,
}


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es-cl'

TIME_ZONE = 'America/Santiago' 
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASS')