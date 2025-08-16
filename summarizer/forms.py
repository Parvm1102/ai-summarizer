from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile


class CustomUserCreationForm(UserCreationForm):
    """Custom registration form with additional fields"""
    email = forms.EmailField(
        required=True,
        help_text="Required for account verification and notifications"
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        help_text="Your first name"
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        help_text="Your last name"
    )
    groq_api_key = forms.CharField(
        max_length=255,
        required=True,
        help_text="Your Groq API key for AI processing",
        widget=forms.TextInput(attrs={'placeholder': 'gsk_...'})
    )
    email_host_user = forms.EmailField(
        required=True,
        help_text="Gmail address for sending summary emails",
        label="Gmail Address"
    )
    email_host_password = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.PasswordInput(attrs={'placeholder': 'Gmail App Password'}),
        help_text="Gmail App Password (not your regular password)",
        label="Gmail App Password"
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes for styling
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field_name in ['password1', 'password2', 'email_host_password']:
                field.widget.attrs['autocomplete'] = 'new-password'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        
        if commit:
            user.save()
            # Create or update user profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.groq_api_key = self.cleaned_data["groq_api_key"]
            profile.email_host_user = self.cleaned_data["email_host_user"]
            profile.email_host_password = self.cleaned_data["email_host_password"]
            profile.save()
        
        return user


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile"""
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = UserProfile
        fields = ['groq_api_key', 'email_host_user', 'email_host_password', 'default_email_signature']
        widgets = {
            'email_host_password': forms.PasswordInput(attrs={'placeholder': 'Gmail App Password'}),
            'default_email_signature': forms.Textarea(attrs={'rows': 4}),
            'groq_api_key': forms.TextInput(attrs={'placeholder': 'gsk_...'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

        # Add CSS classes
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class SummaryForm(forms.Form):
    """Form for creating new summaries"""
    title = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter a title for your summary...'
        })
    )
    summary_type = forms.ChoiceField(
        choices=[
            ('meeting', 'Meeting Notes'),
            ('call', 'Call Transcript'),
            ('document', 'Document'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    custom_prompt = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter custom instructions for AI (e.g., "Summarize in bullet points for executives")...'
        }),
        help_text="Optional: Custom instructions for how you want the AI to summarize the content"
    )
    text_input = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Paste your text content here...'
        }),
        help_text="Paste your text content here, or upload a file below"
    )
    file_upload = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.txt,.md,.docx'
        }),
        help_text="Upload a .txt, .md, or .docx file"
    )

    def clean(self):
        cleaned_data = super().clean()
        text_input = cleaned_data.get('text_input')
        file_upload = cleaned_data.get('file_upload')

        if not text_input and not file_upload:
            raise forms.ValidationError("Please either enter text manually or upload a file.")

        return cleaned_data


class EmailShareForm(forms.Form):
    """Form for sharing summaries via email"""
    recipient_emails = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter email addresses separated by commas...'
        }),
        help_text="Enter multiple email addresses separated by commas"
    )
    custom_message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Add a personal message (optional)...'
        }),
        help_text="Optional personal message to include with the summary"
    )
