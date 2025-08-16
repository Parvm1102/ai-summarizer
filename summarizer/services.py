import time
import logging
from typing import Optional, Dict, Any
from django.conf import settings
from django.utils import timezone
from groq import Groq
from .models import Summary, AIProcessingLog

logger = logging.getLogger(__name__)


class GroqAIService:
    """Service class for handling Groq AI API interactions"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Groq AI service
        
        Args:
            api_key: Groq API key. If not provided, will use default from settings
        """
        self.api_key = api_key or settings.GROQ_API_KEY
        if not self.api_key:
            raise ValueError("Groq API key not provided and not found in settings")
        
        self.client = Groq(api_key=self.api_key)
        self.model = settings.GROQ_DEFAULT_MODEL
    
    def generate_summary(self, summary_obj: Summary) -> Dict[str, Any]:
        """
        Generate a summary using Groq AI
        
        Args:
            summary_obj: Summary model instance
            
        Returns:
            Dict with success status, generated summary, and metadata
        """
        start_time = time.time()
        
        try:
            # Build the prompt
            prompt = self._build_prompt(summary_obj.original_text, summary_obj.custom_prompt)
            
            # Update status to processing
            summary_obj.status = 'processing'
            summary_obj.save(update_fields=['status'])
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at summarizing text. Provide clear, well-structured summaries for the meeting transcript that capture the key points and important details."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2048
            )
            
            processing_time = time.time() - start_time
            
            # Extract the summary
            ai_summary = response.choices[0].message.content.strip()
            
            # Update the summary object
            summary_obj.ai_generated_summary = ai_summary
            summary_obj.status = 'completed'
            summary_obj.processing_time = processing_time
            summary_obj.processed_at = timezone.now()
            summary_obj.save()
            
            # Log the successful processing
            AIProcessingLog.objects.create(
                summary=summary_obj,
                prompt_used=prompt,
                response_received=ai_summary,
                processing_time=processing_time,
                tokens_used=response.usage.total_tokens if hasattr(response, 'usage') else None,
                success=True
            )
            
            logger.info(f"Successfully generated summary for {summary_obj.title} in {processing_time:.2f}s")
            
            return {
                'success': True,
                'summary': ai_summary,
                'processing_time': processing_time,
                'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else None
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            
            # Update summary status to error
            summary_obj.status = 'error'
            summary_obj.save(update_fields=['status'])
            
            # Log the error
            AIProcessingLog.objects.create(
                summary=summary_obj,
                prompt_used=prompt if 'prompt' in locals() else '',
                processing_time=processing_time,
                success=False,
                error_message=error_msg
            )
            
            logger.error(f"Error generating summary for {summary_obj.title}: {error_msg}")
            
            return {
                'success': False,
                'error': error_msg,
                'processing_time': processing_time
            }
    
    def _build_prompt(self, original_text: str, custom_prompt: str) -> str:
        """
        Build the complete prompt for AI processing
        
        Args:
            original_text: The original text to summarize
            custom_prompt: User's custom instruction
            
        Returns:
            Complete prompt string
        """
        if custom_prompt.strip():
            prompt = f"{custom_prompt}\n\nText to summarize:\n{original_text}"
        else:
            prompt = f"{settings.SUMMARIZER_SETTINGS['DEFAULT_PROMPT']}\n\nText to summarize:\n{original_text}"
        
        return prompt
    
    def validate_text_length(self, text: str) -> Dict[str, Any]:
        """
        Validate if text length is within acceptable limits
        
        Args:
            text: Text to validate
            
        Returns:
            Dict with validation status and details
        """
        max_length = settings.SUMMARIZER_SETTINGS['MAX_TEXT_LENGTH']
        text_length = len(text)
        
        if text_length > max_length:
            return {
                'valid': False,
                'error': f'Text length ({text_length:,} characters) exceeds maximum limit ({max_length:,} characters)',
                'text_length': text_length,
                'max_length': max_length
            }
        
        return {
            'valid': True,
            'text_length': text_length,
            'max_length': max_length
        }


def get_user_groq_service(user) -> GroqAIService:
    """
    Get a Groq AI service instance for a specific user
    
    Args:
        user: User instance
        
    Returns:
        GroqAIService instance configured with user's API key or default
    """
    api_key = None
    
    # Try to get API key from user profile
    if hasattr(user, 'userprofile') and user.userprofile.groq_api_key:
        api_key = user.userprofile.groq_api_key
    
    return GroqAIService(api_key=api_key)


def process_summary_async(summary_id: int) -> Dict[str, Any]:
    """
    Process a summary asynchronously (for use with Celery)
    
    Args:
        summary_id: ID of the summary to process
        
    Returns:
        Processing result dictionary
    """
    try:
        summary = Summary.objects.get(id=summary_id)
        service = get_user_groq_service(summary.user)
        return service.generate_summary(summary)
    except Summary.DoesNotExist:
        return {
            'success': False,
            'error': f'Summary with ID {summary_id} not found'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
