import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "123456789")
    
    # Add SERVER_NAME (adjust to your domain or localhost)
    SERVER_NAME = os.getenv('RENDER_EXTERNAL_HOSTNAME', '127.0.0.1:5000')

    PREFERRED_URL_SCHEME = 'https'   # or 'https' for production

    # PostgreSQL Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://postgre:zbZrGbulcnJXapG7eIpLXbG13FR83W2z@dpg-cu9n1llds78s739g1dj0-a/appointments_db_hqko")  # Use Render’s DB URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 20,           # Number of persistent connections
        "max_overflow": 10,        # Extra connections allowed beyond pool size
        "pool_timeout": 30,        # Seconds to wait before giving up
        "pool_recycle": 1800       # Refresh connections every 30 minutes
    }
    #Mail Configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'schoolsucksmg@gmail.com'
    MAIL_PASSWORD = 'crva tufe rwhd pkhq'
    MAIL_DEFAULT_SENDER = 'schoolsucksmg@gmail.com'
