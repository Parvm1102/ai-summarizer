#!/bin/bash

# AI Summarizer Production Startup Script

echo "🚀 Starting AI Summarizer with Gunicorn..."

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate

# Create superuser if it doesn't exist (optional)
# echo "👤 Creating superuser..."
# python manage.py createsuperuser --noinput || true

# Start Gunicorn server
echo "🌟 Starting Gunicorn server..."
gunicorn config.wsgi:application \
    --config gunicorn.conf.py \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --capture-output
