# AI Summarizer

A Django-based web application for AI-powered meeting notes summarization and sharing using the Groq API.

## Features

- **Text Upload**: Upload text transcripts (meeting notes, call transcripts, documents)
- **Custom Prompts**: Input custom instructions for AI processing (e.g., "Summarize in bullet points for executives")
- **AI Summarization**: Generate structured summaries using Groq AI
- **Editable Summaries**: Edit AI-generated summaries before sharing
- **Email Sharing**: Share summaries via email to multiple recipients
- **User Management**: Individual user accounts with API key management
- **Activity Tracking**: Track recent summaries and sharing history

## Tech Stack

- **Backend**: Django 5.2.5
- **AI**: Groq API (Llama models)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Email**: Django email framework
- **File Processing**: Support for .txt, .md, .docx files

## Database Structure

### Models

1. **UserProfile**: Extended user information including Groq API keys
2. **Summary**: Main model storing original text, AI summaries, and user edits
3. **SharedSummaryLog**: Tracks email sharing activities
4. **AIProcessingLog**: Logs AI processing attempts for monitoring

### Key Features of Models

- Automatic word count calculation
- Processing time tracking
- Status management (draft, processing, completed, error)
- Email sharing history
- User-specific API key support

## Installation

1. **Clone and Setup**:
   ```bash
   git clone <repository-url>
   cd ai-summarizer
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Setup**:
   ```bash
   cp .env.example .env
   # Edit .env file with your settings, especially GROQ_API_KEY
   ```

4. **Database Setup**:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py create_sample_data  # Optional: creates test data
   ```

5. **Run Development Server**:
   ```bash
   python manage.py runserver
   ```

6. **Run with Gunicorn (Production-like)**:
   ```bash
   # Option 1: Use the production startup script
   chmod +x start_production.sh
   ./start_production.sh
   
   # Option 2: Run Gunicorn directly
   gunicorn config.wsgi:application --config gunicorn.conf.py
   
   # Option 3: Run Gunicorn with custom settings
   gunicorn config.wsgi:application \
     --bind 0.0.0.0:8000 \
     --workers 4 \
     --timeout 30 \
     --log-level info
   ```

7. **Access Application**:
   - Main app: http://localhost:8000/
   - Admin interface: http://localhost:8000/admin/

## Gunicorn Deployment

### Quick Start with Gunicorn

To start the project with Gunicorn instead of Django's development server:

1. **Using the Production Script** (Recommended):
   ```bash
   chmod +x start_production.sh
   ./start_production.sh
   ```

2. **Direct Gunicorn Command**:
   ```bash
   gunicorn config.wsgi:application --config gunicorn.conf.py
   ```

### Gunicorn Configuration

The project includes a `gunicorn.conf.py` file with optimized settings:

- **Bind Address**: `0.0.0.0:8000` (accessible from any IP)
- **Workers**: Auto-calculated based on CPU cores (2 * cores + 1)
- **Worker Class**: `sync` (suitable for Django apps)
- **Timeout**: 30 seconds
- **Logging**: Configured for both access and error logs

### Custom Gunicorn Commands

```bash
# Start with specific number of workers
gunicorn config.wsgi:application --workers 4 --bind 0.0.0.0:8000

# Start with custom timeout
gunicorn config.wsgi:application --timeout 60 --bind 0.0.0.0:8000

# Start in daemon mode (background)
gunicorn config.wsgi:application --config gunicorn.conf.py --daemon

# Start with reload (development)
gunicorn config.wsgi:application --reload --bind 0.0.0.0:8000
```

### Environment Setup for Gunicorn

Ensure you have the required dependencies:
```bash
pip install gunicorn
# All other dependencies are in requirements.txt
```

## Configuration

### Required Settings

- `GROQ_API_KEY`: Your Groq API key for AI processing
- `EMAIL_HOST_USER` & `EMAIL_HOST_PASSWORD`: For email sharing (production)

### Optional Settings

- `MAX_UPLOAD_SIZE`: Maximum file upload size (default: 5MB)
- `MAX_TEXT_LENGTH`: Maximum text length for processing (default: 100k chars)
- `GROQ_DEFAULT_MODEL`: AI model to use (default: llama3-8b-8192)

## Usage

### Admin Interface

1. Access admin at `/admin/` with superuser credentials
2. Manage users and their profiles
3. View summaries and processing logs
4. Monitor email sharing activities

### API Keys

- Global API key can be set in Django settings
- Individual users can set their own API keys in their profiles
- User-specific keys take precedence over global settings

### File Uploads

Supported formats:
- `.txt`: Plain text files
- `.md`: Markdown files
- `.docx`: Microsoft Word documents

### Sample Data

Use the management command to create test data:
```bash
python manage.py create_sample_data --user admin
```

## Development

### Adding New File Types

1. Update `SUPPORTED_FILE_TYPES` in settings
2. Add extraction logic in `summarizer/utils.py`
3. Install any required packages

### Custom AI Prompts

Users can provide custom instructions like:
- "Summarize in bullet points for executives"
- "Highlight only action items"
- "Focus on technical decisions and next steps"

### Email Templates

Email content is generated in `summarizer/email_service.py`. Customize the `_create_email_body` method for different formats.

## Production Deployment

1. Set `DEBUG=False` in settings
2. Configure proper database (PostgreSQL recommended)
3. Set up email backend (SMTP)
4. Configure static files serving
5. Set up proper logging
6. Use environment variables for sensitive settings

## Security Notes

- API keys are stored encrypted in the database
- File uploads are validated for type and size
- Email addresses are validated before sending
- User isolation: users can only see their own data

## Troubleshooting

### Common Issues

1. **Groq API errors**: Check API key and quota
2. **File upload fails**: Check file size and format
3. **Email not sending**: Verify SMTP settings
4. **Import errors**: Ensure all dependencies are installed

### Logs

- Check Django logs for application errors
- AI processing logs are stored in `AIProcessingLog` model
- Email sending logs in `SharedSummaryLog` model

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

[Add your license information here]
