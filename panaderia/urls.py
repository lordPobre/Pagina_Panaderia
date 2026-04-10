from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from core import views 

urlpatterns = [
    path('perseus-access-x12', admin.site.urls),
    path('', views.home, name='home'),
    path('', include('core.urls')), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
