"""Root URL configuration."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(_request):
    """Lightweight liveness probe."""
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health),

    path('api/auth/', include('accounts.urls')),
    path('api/documents/', include('documents.urls')),
    path('api/blog/', include('blog.urls')),
    path('api/subscriptions/', include('subscriptions.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/admin-panel/', include('admin_panel.urls')),
]

# Serve uploaded media locally in development (when not using S3).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
