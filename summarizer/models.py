from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    """Extended user profile for additional information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    groq_api_key = models.CharField(max_length=255, blank=True, null=True, help_text="User's Groq API key for AI processing")
    default_email_signature = models.TextField(blank=True, null=True, help_text="Default signature for email sharing")
    
    # Email configuration for sending summaries
    email_host_user = models.EmailField(blank=True, null=True, help_text="Gmail address for sending emails")
    email_host_password = models.CharField(max_length=255, blank=True, null=True, help_text="Gmail app password")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


class Summary(models.Model):
    """Model to store AI-generated summaries and user edits"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('error', 'Error'),
    ]
    
    TYPE_CHOICES = [
        ('meeting', 'Meeting Notes'),
        ('call', 'Call Transcript'),
        ('document', 'Document'),
        ('other', 'Other'),
    ]

    # Basic Information
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='summaries')
    title = models.CharField(max_length=255, help_text="Title of the summary")
    summary_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='meeting')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Content
    original_text = models.TextField(help_text="Original uploaded text/transcript")
    custom_prompt = models.TextField(help_text="Custom instruction/prompt for AI processing")
    ai_generated_summary = models.TextField(blank=True, null=True, help_text="AI-generated summary")
    edited_summary = models.TextField(blank=True, null=True, help_text="User-edited version of the summary")
    
    # Metadata
    word_count_original = models.PositiveIntegerField(default=0, help_text="Word count of original text")
    word_count_summary = models.PositiveIntegerField(default=0, help_text="Word count of final summary")
    processing_time = models.FloatField(blank=True, null=True, help_text="Time taken for AI processing in seconds")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(blank=True, null=True, help_text="When AI processing was completed")
    
    # Sharing
    is_shared = models.BooleanField(default=False, help_text="Whether this summary has been shared")
    shared_at = models.DateTimeField(blank=True, null=True, help_text="When the summary was last shared")
    shared_with_emails = models.TextField(blank=True, null=True, help_text="Comma-separated list of emails shared with")

    def save(self, *args, **kwargs):
        # Auto-calculate word counts
        if self.original_text:
            self.word_count_original = len(self.original_text.split())
        
        final_summary = self.edited_summary or self.ai_generated_summary
        if final_summary:
            self.word_count_summary = len(final_summary.split())
        
        super().save(*args, **kwargs)

    def get_final_summary(self):
        """Returns the edited summary if available, otherwise the AI-generated summary"""
        return self.edited_summary or self.ai_generated_summary

    def mark_as_shared(self, emails):
        """Mark the summary as shared with given emails"""
        self.is_shared = True
        self.shared_at = timezone.now()
        self.shared_with_emails = ', '.join(emails) if isinstance(emails, list) else emails
        self.save(update_fields=['is_shared', 'shared_at', 'shared_with_emails'])

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    class Meta:
        verbose_name = "Summary"
        verbose_name_plural = "Summaries"
        ordering = ['-created_at']


class SharedSummaryLog(models.Model):
    """Log of when summaries are shared via email"""
    summary = models.ForeignKey(Summary, on_delete=models.CASCADE, related_name='share_logs')
    recipient_emails = models.TextField(help_text="Comma-separated list of recipient emails")
    subject = models.CharField(max_length=255, help_text="Email subject line")
    message_body = models.TextField(blank=True, null=True, help_text="Additional message body")
    shared_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True, help_text="Whether the email was sent successfully")
    error_message = models.TextField(blank=True, null=True, help_text="Error message if email failed")

    def __str__(self):
        return f"Shared '{self.summary.title}' on {self.shared_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = "Shared Summary Log"
        verbose_name_plural = "Shared Summary Logs"
        ordering = ['-shared_at']


class AIProcessingLog(models.Model):
    """Log of AI processing attempts for debugging and monitoring"""
    summary = models.ForeignKey(Summary, on_delete=models.CASCADE, related_name='processing_logs')
    prompt_used = models.TextField(help_text="The full prompt sent to AI")
    response_received = models.TextField(blank=True, null=True, help_text="Raw AI response")
    processing_time = models.FloatField(help_text="Processing time in seconds")
    tokens_used = models.PositiveIntegerField(blank=True, null=True, help_text="Number of tokens used")
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "Success" if self.success else "Error"
        return f"{status} - {self.summary.title} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

    class Meta:
        verbose_name = "AI Processing Log"
        verbose_name_plural = "AI Processing Logs"
        ordering = ['-created_at']
