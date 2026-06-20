"""Root URL configuration."""
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

    # API routes are added per-phase:
    # path('api/subscriptions/', include('subscriptions.urls')),
    # path('api/documents/',     include('documents.urls')),
    # path('api/ai/',            include('ai_engine.urls')),
    # path('api/blog/',          include('blog.urls')),
    # path('api/payments/',      include('payments.urls')),
    # path('api/admin-panel/',   include('admin_panel.urls')),
]
