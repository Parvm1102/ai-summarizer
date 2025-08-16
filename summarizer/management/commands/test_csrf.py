"""
Management command to test CSRF configuration
"""
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Test CSRF configuration'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('CSRF Configuration Test'))
        self.stdout.write(f"DEBUG: {settings.DEBUG}")
        self.stdout.write(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        self.stdout.write(f"CSRF_COOKIE_SECURE: {getattr(settings, 'CSRF_COOKIE_SECURE', 'Not Set')}")
        self.stdout.write(f"CSRF_COOKIE_HTTPONLY: {getattr(settings, 'CSRF_COOKIE_HTTPONLY', 'Not Set')}")
        self.stdout.write(f"CSRF_COOKIE_SAMESITE: {getattr(settings, 'CSRF_COOKIE_SAMESITE', 'Not Set')}")
        self.stdout.write(f"CSRF_TRUSTED_ORIGINS: {getattr(settings, 'CSRF_TRUSTED_ORIGINS', 'Not Set')}")
        self.stdout.write(f"SESSION_COOKIE_SECURE: {getattr(settings, 'SESSION_COOKIE_SECURE', 'Not Set')}")
        
        self.stdout.write(self.style.SUCCESS('Test completed successfully!'))
