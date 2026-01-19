"""
============================================================
🔗 SIGEM - URLs Principais
============================================================
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin do Django
    path('admin/', admin.site.urls),
    
    # URLs do app missoes (principal)
    path('', include('missoes.urls')),
]

# Servir arquivos de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
