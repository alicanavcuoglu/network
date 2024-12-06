import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")
    SECURITY_PASSWORD_SALT = os.getenv(
        "SECURITY_PASSWORD_SALT", default="very-important"
    )

    MAX_CONTENT_LENGTH = 1024 * 1024  # 1 MB

    # Mail Settings
    # MAIL_SERVER = "smtp.mailgun.org"
    # MAIL_PORT = 587
    # MAIL_USE_TLS = True
    # MAIL_USERNAME = os.getenv("EMAIL_USER")
    # MAIL_PASSWORD = os.getenv("MAILGUN_API_KEY")
    # MAIL_DEFAULT_SENDER = os.getenv("EMAIL_USER")
    # MAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


class ProductionConfig(Config):
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_POOL_TIMEOUT = 30
    SQLALCHEMY_POOL_RECYCLE = 1800
    SQLALCHEMY_MAX_OVERFLOW = 20
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_DOMAIN = "cssocial50.com"
    SESSION_COOKIE_SAMESITE = "Lax"
