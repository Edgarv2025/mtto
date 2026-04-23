class Config:
    SECRET_KEY = "super_secret_key_mtto_123"
    DB_PATH = "maintenance.db"
    
    # Email Config
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_USER = "artyento@gmail.com"
    EMAIL_PASSWORD = "ElDj2023"
    
    # Default fallback email for notifications
    DEFAULT_NOTIFY_EMAIL = "evasquez@imasa.com.co"
