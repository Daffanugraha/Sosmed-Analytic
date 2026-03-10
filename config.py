import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production-2024')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'data', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}
    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}

    # ─── Platform OAuth Credentials ──────────────────────────────────
    # Instagram / Facebook (same Facebook App)
    INSTAGRAM_CLIENT_ID     = os.environ.get('INSTAGRAM_CLIENT_ID', '')
    INSTAGRAM_CLIENT_SECRET = os.environ.get('INSTAGRAM_CLIENT_SECRET', '')
    FACEBOOK_CLIENT_ID      = os.environ.get('FACEBOOK_CLIENT_ID', '')
    FACEBOOK_CLIENT_SECRET  = os.environ.get('FACEBOOK_CLIENT_SECRET', '')

    # TikTok
    TIKTOK_CLIENT_KEY    = os.environ.get('TIKTOK_CLIENT_KEY', '')
    TIKTOK_CLIENT_SECRET = os.environ.get('TIKTOK_CLIENT_SECRET', '')

    # YouTube / Google
    YOUTUBE_CLIENT_ID     = os.environ.get('YOUTUBE_CLIENT_ID', '')
    YOUTUBE_CLIENT_SECRET = os.environ.get('YOUTUBE_CLIENT_SECRET', '')

    # Base URL (used for OAuth redirect URIs)
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
