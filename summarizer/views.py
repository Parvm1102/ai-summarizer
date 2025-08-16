from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db import models
from .models import Summary, UserProfile, AIProcessingLog, SharedSummaryLog
from .forms import CustomUserCreationForm, UserProfileForm, SummaryForm, EmailShareForm
from .services import get_user_groq_service
from .email_service import EmailService
from .utils import FileProcessor


def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})


def home(request):
    """Home page view"""
    if request.user.is_authenticated:
        return redirect('summarizer:dashboard')
    return render(request, 'summarizer/home.html')


@login_required
def dashboard(request):
    """User dashboard showing recent summaries"""
    summaries = Summary.objects.filter(user=request.user).order_by('-created_at')
    
    # Get recent summaries for preview
    recent_summaries = summaries[:5]
    
    # Calculate statistics
    total_summaries = summaries.count()
    completed_summaries = summaries.filter(status='completed').count()
    pending_summaries = summaries.filter(status__in=['draft', 'processing']).count()
    shared_summaries = summaries.filter(is_shared=True).count()
    
    context = {
        'recent_summaries': recent_summaries,
        'total_summaries': total_summaries,
        'completed_summaries': completed_summaries,
        'pending_summaries': pending_summaries,
        'shared_summaries': shared_summaries,
    }
    
    return render(request, 'summarizer/dashboard.html', context)


@login_required
def history(request):
    """History page showing all summaries with pagination"""
    summaries = Summary.objects.filter(user=request.user).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        summaries = summaries.filter(
            models.Q(title__icontains=search_query) |
            models.Q(original_text__icontains=search_query) |
            models.Q(ai_generated_summary__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        summaries = summaries.filter(status=status_filter)
    
    # Paginate summaries
    paginator = Paginator(summaries, 10)  # Show 10 summaries per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': Summary.STATUS_CHOICES,
    }
    
    return render(request, 'summarizer/history.html', context)


@login_required
def create_summary(request):
    """Create a new summary"""
    if request.method == 'POST':
        form = SummaryForm(request.POST, request.FILES)
        if form.is_valid():
            title = form.cleaned_data['title']
            summary_type = form.cleaned_data['summary_type']
            custom_prompt = form.cleaned_data['custom_prompt']
            text_input = form.cleaned_data['text_input']
            uploaded_file = form.cleaned_data['file_upload']
            
            # Get text content
            original_text = ''
            if uploaded_file:
                # Process uploaded file
                result = FileProcessor.extract_text_from_file(uploaded_file)
                if result['success']:
                    original_text = result['text']
                    messages.success(request, f'Successfully extracted {result["word_count"]} words from {result["file_name"]}')
                else:
                    messages.error(request, f'File processing error: {result["error"]}')
                    return render(request, 'summarizer/create_summary.html', {'form': form})
            else:
                original_text = text_input
            
            # Validate text length
            groq_service = get_user_groq_service(request.user)
            validation = groq_service.validate_text_length(original_text)
            if not validation['valid']:
                messages.error(request, validation['error'])
                return render(request, 'summarizer/create_summary.html', {'form': form})
            
            # Create summary
            summary = Summary.objects.create(
                user=request.user,
                title=title,
                summary_type=summary_type,
                original_text=original_text,
                custom_prompt=custom_prompt or "Please summarize the following text in a clear and concise manner:",
                status='draft'
            )
            
            messages.success(request, f'Summary "{title}" created successfully!')
            return redirect('summarizer:view_summary', summary_id=summary.id)
    else:
        form = SummaryForm()
    
    return render(request, 'summarizer/create_summary.html', {'form': form})


@login_required
def view_summary(request, summary_id):
    """View a specific summary"""
    summary = get_object_or_404(Summary, id=summary_id, user=request.user)
    
    context = {
        'summary': summary,
        'final_summary': summary.get_final_summary(),
        'processing_logs': summary.processing_logs.all().order_by('-created_at')[:5],
        'share_logs': summary.share_logs.all().order_by('-shared_at')[:5],
        'email_form': EmailShareForm(),
    }
    
    return render(request, 'summarizer/view_summary.html', context)


@login_required
@require_http_methods(["POST"])
def generate_summary(request, summary_id):
    """Generate AI summary for a specific summary object"""
    summary = get_object_or_404(Summary, id=summary_id, user=request.user)
    
    if summary.status == 'processing':
        return JsonResponse({
            'success': False,
            'error': 'Summary is already being processed'
        })
    
    try:
        groq_service = get_user_groq_service(request.user)
        result = groq_service.generate_summary(summary)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'summary': result['summary'],
                'processing_time': result['processing_time'],
                'message': 'Summary generated successfully!'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result['error']
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def edit_summary(request, summary_id):
    """Edit the AI-generated summary"""
    summary = get_object_or_404(Summary, id=summary_id, user=request.user)
    
    edited_content = request.POST.get('edited_summary', '').strip()
    
    if not edited_content:
        return JsonResponse({
            'success': False,
            'error': 'Edited summary cannot be empty'
        })
    
    summary.edited_summary = edited_content
    summary.save(update_fields=['edited_summary', 'updated_at'])
    
    return JsonResponse({
        'success': True,
        'message': 'Summary updated successfully!'
    })


@login_required
@require_http_methods(["POST"])
def share_summary(request, summary_id):
    """Share summary via email"""
    summary = get_object_or_404(Summary, id=summary_id, user=request.user)
    
    form = EmailShareForm(request.POST)
    if form.is_valid():
        recipient_emails_str = form.cleaned_data['recipient_emails']
        custom_message = form.cleaned_data['custom_message']
        
        # Parse and validate email addresses
        recipient_emails = EmailService.parse_email_list(recipient_emails_str)
        validation = EmailService.validate_email_addresses(recipient_emails)
        
        if not validation['valid']:
            return JsonResponse({
                'success': False,
                'error': f'Invalid email addresses: {", ".join(validation["invalid_emails"])}'
            })
        
        # Send emails using user's Gmail configuration
        sender_name = request.user.get_full_name() or request.user.username
        result = EmailService.share_summary_via_email(
            summary=summary,
            recipient_emails=validation['valid_emails'],
            custom_message=custom_message,
            sender_name=sender_name,
            user_profile=request.user.userprofile
        )
        
        if result['success']:
            messages.success(request, result['message'])
            return JsonResponse({
                'success': True,
                'message': result['message']
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Unknown error occurred'),
                'details': result
            })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Form validation failed',
            'form_errors': form.errors
        })


@login_required
def user_profile(request):
    """User profile page"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            # Update user fields
            request.user.first_name = form.cleaned_data.get('first_name', '')
            request.user.last_name = form.cleaned_data.get('last_name', '')
            request.user.email = form.cleaned_data.get('email', '')
            request.user.save()
            
            # Update profile
            form.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('summarizer:user_profile')
    else:
        form = UserProfileForm(instance=profile, user=request.user)
    
    # Calculate user statistics
    summaries = Summary.objects.filter(user=request.user)
    stats = {
        'total_summaries': summaries.count(),
        'completed_summaries': summaries.filter(status='completed').count(),
        'shared_summaries': summaries.filter(is_shared=True).count(),
        'total_words_processed': sum(s.word_count_original for s in summaries),
        'join_date': request.user.date_joined,
    }
    
    context = {
        'form': form,
        'profile': profile,
        'stats': stats,
    }
    
    return render(request, 'summarizer/profile.html', context)


def logout_view(request):
    """Custom logout view that handles both GET and POST requests"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('summarizer:home')


# Legacy method name for compatibility
user_settings = user_profile
