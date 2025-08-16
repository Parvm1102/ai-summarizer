"""
CSRF Helper views
"""
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
@require_http_methods(["GET"])
def get_csrf_token(request):
    """
    Get CSRF token for AJAX requests
    """
    return JsonResponse({
        'csrfToken': get_token(request)
    })


@ensure_csrf_cookie
def csrf_failure_view(request, reason=""):
    """
    Custom CSRF failure view
    """
    return JsonResponse({
        'error': 'CSRF verification failed',
        'reason': reason,
        'reload_required': True
    }, status=403)
