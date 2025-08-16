import logging
from typing import List, Dict, Any
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Summary, SharedSummaryLog

logger = logging.getLogger(__name__)


class EmailService:
    """Service class for handling email functionality"""
    
    @staticmethod
    def share_summary_via_email(
        summary: Summary, 
        recipient_emails: List[str], 
        custom_message: str = "",
        sender_name: str = "",
        user_profile = None
    ) -> Dict[str, Any]:
        """
        Share a summary via email using user's Gmail configuration
        
        Args:
            summary: Summary instance to share
            recipient_emails: List of recipient email addresses
            custom_message: Optional custom message to include
            sender_name: Name of the person sharing (optional)
            user_profile: UserProfile instance with email credentials
            
        Returns:
            Dict with success status and details
        """
        try:
            # Prepare email content
            subject = f"Summary: {summary.title}"
            
            # Get the final summary (edited version if available, otherwise AI-generated)
            final_summary = summary.get_final_summary()
            
            if not final_summary:
                return {
                    'success': False,
                    'error': 'No summary content available to share'
                }
            
            # Prepare context for email template
            context = {
                'summary': summary,
                'final_summary': final_summary,
                'custom_message': custom_message,
                'sender_name': sender_name or summary.user.get_full_name() or summary.user.username,
                'shared_at': timezone.now(),
                'word_count': summary.word_count_summary,
                'original_word_count': summary.word_count_original
            }
            
            # Create email body
            email_body = EmailService._create_email_body(context)
            
            # Use user's Gmail configuration if available
            from django.core.mail import get_connection
            
            if user_profile and user_profile.email_host_user and user_profile.email_host_password:
                # Use user's Gmail settings
                connection = get_connection(
                    backend='django.core.mail.backends.smtp.EmailBackend',
                    host='smtp.gmail.com',
                    port=587,
                    use_tls=True,
                    username=user_profile.email_host_user,
                    password=user_profile.email_host_password,
                    fail_silently=False,
                )
                from_email = user_profile.email_host_user
            else:
                # Use default settings
                connection = get_connection()
                from_email = settings.DEFAULT_FROM_EMAIL
            
            # Send email
            success_count = 0
            failed_emails = []
            
            for email in recipient_emails:
                try:
                    from django.core.mail import EmailMessage
                    
                    email_message = EmailMessage(
                        subject=subject,
                        body=email_body,
                        from_email=from_email,
                        to=[email],
                        connection=connection,
                    )
                    email_message.send()
                    success_count += 1
                except Exception as e:
                    failed_emails.append({'email': email, 'error': str(e)})
                    logger.error(f"Failed to send email to {email}: {e}")
            
            # Log the sharing attempt
            SharedSummaryLog.objects.create(
                summary=summary,
                recipient_emails=', '.join(recipient_emails),
                subject=subject,
                message_body=custom_message,
                success=len(failed_emails) == 0,
                error_message='; '.join([f"{item['email']}: {item['error']}" for item in failed_emails]) if failed_emails else None
            )
            
            # Update summary sharing status
            if success_count > 0:
                summary.mark_as_shared(recipient_emails)
            
            if failed_emails:
                return {
                    'success': False,
                    'partial_success': success_count > 0,
                    'success_count': success_count,
                    'failed_emails': failed_emails,
                    'message': f'Sent to {success_count} recipients, failed for {len(failed_emails)} recipients'
                }
            else:
                return {
                    'success': True,
                    'success_count': success_count,
                    'message': f'Successfully sent to all {success_count} recipients'
                }
                
        except Exception as e:
            logger.error(f"Error sharing summary {summary.id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def _create_email_body(context: Dict[str, Any]) -> str:
        """
        Create the email body content
        
        Args:
            context: Template context dictionary
            
        Returns:
            Email body string
        """
        summary = context['summary']
        final_summary = context['final_summary']
        custom_message = context['custom_message']
        sender_name = context['sender_name']
        shared_at = context['shared_at']
        
        # Create a simple text email body
        email_lines = []
        
        if custom_message:
            email_lines.append(f"Message from {sender_name}:")
            email_lines.append(custom_message)
            email_lines.append("")
        
        email_lines.extend([
            f"Summary: {summary.title}",
            f"Type: {summary.get_summary_type_display()}",
            f"Created: {summary.created_at.strftime('%B %d, %Y at %I:%M %p')}",
            f"Shared by: {sender_name}",
            f"Shared on: {shared_at.strftime('%B %d, %Y at %I:%M %p')}",
            "",
            "=" * 50,
            "SUMMARY CONTENT",
            "=" * 50,
            "",
            final_summary,
            "",
            "=" * 50,
            "",
            f"Original text: {context['original_word_count']} words",
            f"Summary: {context['word_count']} words",
            "",
            "This summary was generated using AI Summarizer.",
        ])
        
        return "\n".join(email_lines)
    
    @staticmethod
    def validate_email_addresses(emails: List[str]) -> Dict[str, Any]:
        """
        Validate a list of email addresses
        
        Args:
            emails: List of email addresses to validate
            
        Returns:
            Dict with validation results
        """
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        valid_emails = []
        invalid_emails = []
        
        for email in emails:
            email = email.strip()
            if not email:
                continue
                
            try:
                validate_email(email)
                valid_emails.append(email)
            except ValidationError:
                invalid_emails.append(email)
        
        return {
            'valid': len(invalid_emails) == 0,
            'valid_emails': valid_emails,
            'invalid_emails': invalid_emails,
            'total_count': len(emails),
            'valid_count': len(valid_emails),
            'invalid_count': len(invalid_emails)
        }
    
    @staticmethod
    def parse_email_list(email_string: str) -> List[str]:
        """
        Parse a string of emails separated by commas, semicolons, or spaces
        
        Args:
            email_string: String containing email addresses
            
        Returns:
            List of email addresses
        """
        import re
        
        # Replace semicolons and multiple spaces with commas
        normalized = re.sub(r'[;\s]+', ',', email_string.strip())
        
        # Split by comma and clean up
        emails = [email.strip() for email in normalized.split(',') if email.strip()]
        
        return emails
