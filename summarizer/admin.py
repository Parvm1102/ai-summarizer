from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Summary, SharedSummaryLog, AIProcessingLog


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('groq_api_key', 'default_email_signature')


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)


# Unregister the original User admin and register the custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'summary_type', 'status', 'word_count_original', 'word_count_summary', 'is_shared', 'created_at')
    list_filter = ('summary_type', 'status', 'is_shared', 'created_at', 'updated_at')
    search_fields = ('title', 'user__username', 'original_text', 'ai_generated_summary', 'edited_summary')
    readonly_fields = ('word_count_original', 'word_count_summary', 'processing_time', 'created_at', 'updated_at', 'processed_at', 'shared_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'summary_type', 'status')
        }),
        ('Content', {
            'fields': ('original_text', 'custom_prompt', 'ai_generated_summary', 'edited_summary')
        }),
        ('Metadata', {
            'fields': ('word_count_original', 'word_count_summary', 'processing_time'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'processed_at'),
            'classes': ('collapse',)
        }),
        ('Sharing', {
            'fields': ('is_shared', 'shared_at', 'shared_with_emails'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(user=request.user)
        return queryset


@admin.register(SharedSummaryLog)
class SharedSummaryLogAdmin(admin.ModelAdmin):
    list_display = ('summary', 'recipient_emails', 'subject', 'success', 'shared_at')
    list_filter = ('success', 'shared_at')
    search_fields = ('summary__title', 'recipient_emails', 'subject')
    readonly_fields = ('shared_at',)
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(summary__user=request.user)
        return queryset


@admin.register(AIProcessingLog)
class AIProcessingLogAdmin(admin.ModelAdmin):
    list_display = ('summary', 'success', 'processing_time', 'tokens_used', 'created_at')
    list_filter = ('success', 'created_at')
    search_fields = ('summary__title', 'error_message')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('summary', 'success', 'processing_time', 'tokens_used', 'created_at')
        }),
        ('Processing Details', {
            'fields': ('prompt_used', 'response_received', 'error_message'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(summary__user=request.user)
        return queryset
