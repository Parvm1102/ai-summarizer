# Gunicorn configuration file
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = 1  # Use single worker for development to avoid session issues
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 60
max_requests = 1000
max_requests_jitter = 50

# Restart workers after this many requests, to help prevent memory leaks
preload_app = True

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'ai_summarizer'

# Server mechanics
daemon = False
pidfile = '/tmp/gunicorn.pid'
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = None
# certfile = None
