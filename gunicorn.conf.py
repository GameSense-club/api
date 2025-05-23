bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
timeout = 30
keepalive = 2

# Логирование
accesslog = "/var/log/gamesense-api/access.log"
errorlog = "/var/log/gamesense-api/error.log"
loglevel = "info"

# Безопасность
user = "www-data"
group = "www-data"
umask = 0o007

raw_env = [
    "FLASK_ENV=production",
]

reload = False