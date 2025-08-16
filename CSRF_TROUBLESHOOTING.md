# CSRF Troubleshooting Guide

## The Problem
You're getting "CSRF verification failed" when trying to login on your deployed website.

## Solutions

### 1. **Immediate Fix for Deployment**

Add your deployment URL to `CSRF_TRUSTED_ORIGINS` in your production environment variables:

```bash
# In your deployment platform (Render, Heroku, etc.)
CSRF_TRUSTED_ORIGINS=https://your-app-name.onrender.com,https://your-custom-domain.com
```

### 2. **Update Environment Variables on Render**

In your Render dashboard, add these environment variables:

```
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True
CSRF_TRUSTED_ORIGINS=https://your-app-name.onrender.com
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
```

### 3. **For Local Development**

In your `.env` file, ensure these are set correctly:

```
DEBUG=True
CSRF_COOKIE_SECURE=False
SESSION_COOKIE_SECURE=False
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
```

### 4. **Test CSRF Configuration**

Run this command to check your CSRF settings:

```bash
python manage.py test_csrf
```

### 5. **Quick Test URL**

Visit `https://your-app.onrender.com/csrf-token/` to get a fresh CSRF token.

## Common Causes & Fixes

### Issue: "Forbidden (403) CSRF verification failed"

**Cause**: Your deployment domain is not in `CSRF_TRUSTED_ORIGINS`

**Fix**: Add your exact deployment URL to `CSRF_TRUSTED_ORIGINS`:
```python
CSRF_TRUSTED_ORIGINS = [
    'https://your-app-name.onrender.com',
    'https://www.your-domain.com',
]
```

### Issue: CSRF token missing or invalid

**Cause**: Form doesn't have `{% csrf_token %}` or JavaScript isn't sending the token

**Fix**: Ensure all forms include:
```html
<form method="post">
    {% csrf_token %}
    <!-- form fields -->
</form>
```

### Issue: Mixed HTTP/HTTPS content

**Cause**: App is served over HTTPS but some requests are HTTP

**Fix**: Set these in production:
```python
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

## Testing Steps

1. **Check your deployment URL**:
   - Make sure you're using the exact URL (with https://)
   - No trailing slashes if not needed

2. **Clear browser cache**:
   - Hard refresh (Ctrl+F5)
   - Clear cookies for your site

3. **Check browser console**:
   - Look for CSRF-related errors
   - Check if CSRF token is being sent

4. **Test login form**:
   - View page source
   - Confirm `<input type="hidden" name="csrfmiddlewaretoken" value="...">` exists

## Emergency Bypass (DEVELOPMENT ONLY)

If you need to temporarily disable CSRF for testing:

1. Create a custom middleware
2. Add `@csrf_exempt` to specific views
3. **NEVER** use this in production

## Contact Support

If issues persist, check:
1. Django logs on your deployment platform
2. Browser network tab for failed requests
3. Deployment platform logs (Render logs, Heroku logs, etc.)
