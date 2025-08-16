"""
Custom middleware for handling CSRF and session errors
"""
import logging
from django.http import JsonResponse
from django.middleware.csrf import CsrfViewMiddleware
from django.conf import settings

logger = logging.getLogger(__name__)


class ImprovedCsrfMiddleware(CsrfViewMiddleware):
    """
    Improved CSRF middleware that provides better error handling
    """
    
    def process_view(self, request, callback, callback_args, callback_kwargs):
        try:
            return super().process_view(request, callback, callback_args, callback_kwargs)
        except Exception as e:
            logger.error(f"CSRF Error: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Security token expired. Please refresh the page and try again.',
                    'reload_required': True
                }, status=403)
            return None


class SessionErrorMiddleware:
    """
    Middleware to handle session-related errors gracefully
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            logger.error(f"Session Error: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Session error occurred. Please refresh the page and try again.',
                    'reload_required': True
                }, status=500)
            raise
