# Database Setup Guide for AI Summarizer

## 🚀 Recommended Approach

### For Render Deployment: **USE POSTGRESQL** ✅

**Why PostgreSQL?**
- ✅ Data persists through deployments
- ✅ Handles multiple concurrent users
- ✅ Automatic backups on Render
- ✅ Free tier available
- ✅ Production-ready

### For Local Development: **USE SQLITE** ✅
- ✅ No setup required
- ✅ Perfect for development
- ✅ Easy database resets

## 📋 Setup Instructions

### 1. Local Development (SQLite)
Create `.env` file:
```bash
USE_SQLITE=True
SECRET_KEY=your-local-secret-key
DEBUG=True
GROQ_API_KEY=your_groq_api_key
```

### 2. Render Production (PostgreSQL)
On Render Dashboard:
1. Create PostgreSQL database (free tier)
2. In your web service, set environment variables:
```bash
DATABASE_URL=postgresql://... (auto-provided by Render)
USE_SQLITE=False
SECRET_KEY=your-production-secret-key
DEBUG=False
GROQ_API_KEY=your_groq_api_key
```

### 3. Alternative: Manual PostgreSQL Config
If not using DATABASE_URL:
```bash
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=5432
```

## 🎯 Migration Commands

### Migrate to PostgreSQL:
```bash
# 1. Set up PostgreSQL credentials in .env
# 2. Run migrations
python manage.py migrate

# 3. Create superuser (optional)
python manage.py createsuperuser
```

### Reset Database (SQLite only):
```bash
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

## 💡 Pro Tips

1. **Keep SQLite for local development** - faster and easier
2. **Use PostgreSQL for production** - more reliable and scalable
3. **Render automatically provides DATABASE_URL** - easiest setup
4. **Free PostgreSQL tier** - perfect for starting out
5. **Automatic backups** - peace of mind for production data

## ⚠️ Important Notes

- **SQLite data will be lost on Render** when containers restart
- **PostgreSQL data persists** through deployments and restarts
- **Environment variables** control which database to use
- **No code changes needed** - just environment configuration
