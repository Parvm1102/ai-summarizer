from django.urls import path
from . import views
from . import csrf_views

app_name = 'summarizer'

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('history/', views.history, name='history'),
    
    # Summary management
    path('create/', views.create_summary, name='create_summary'),
    path('summary/<int:summary_id>/', views.view_summary, name='view_summary'),
    
    # AJAX endpoints
    path('summary/<int:summary_id>/generate/', views.generate_summary, name='generate_summary'),
    path('summary/<int:summary_id>/edit/', views.edit_summary, name='edit_summary'),
    path('summary/<int:summary_id>/share/', views.share_summary, name='share_summary'),
    
    # CSRF helper endpoints
    path('csrf-token/', csrf_views.get_csrf_token, name='csrf_token'),
    
    # User profile and settings
    path('profile/', views.user_profile, name='user_profile'),
    path('settings/', views.user_settings, name='user_settings'),  # Legacy compatibility
]
