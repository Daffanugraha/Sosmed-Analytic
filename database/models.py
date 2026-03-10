from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name     = db.Column(db.String(120))
    avatar        = db.Column(db.String(255))
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    platform_accounts = db.relationship('PlatformAccount', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    posts             = db.relationship('Post', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class PlatformAccount(db.Model):
    """Stores connected social media accounts per user."""
    __tablename__ = 'platform_accounts'

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    platform      = db.Column(db.String(30), nullable=False)   # instagram | tiktok | facebook | youtube
    account_id    = db.Column(db.String(255))                  # platform's own user/page id
    account_name  = db.Column(db.String(255))
    account_email = db.Column(db.String(255))
    avatar_url    = db.Column(db.String(500))
    access_token  = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    token_expiry  = db.Column(db.DateTime)
    extra_data    = db.Column(db.Text)                         # JSON for platform-specific data
    is_active     = db.Column(db.Boolean, default=True)
    connected_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_extra_data(self):
        if self.extra_data:
            return json.loads(self.extra_data)
        return {}

    def set_extra_data(self, data: dict):
        self.extra_data = json.dumps(data)

    def __repr__(self):
        return f'<PlatformAccount {self.platform}:{self.account_name}>'


class Post(db.Model):
    """A content post that can be published to multiple platforms."""
    __tablename__ = 'posts'

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title        = db.Column(db.String(255))
    caption      = db.Column(db.Text)
    hashtags     = db.Column(db.Text)
    media_files  = db.Column(db.Text)          # JSON list of file paths
    media_type   = db.Column(db.String(20))    # video | image
    status       = db.Column(db.String(30), default='draft')  # draft|scheduled|publishing|published|failed
    scheduled_at = db.Column(db.DateTime)
    published_at = db.Column(db.DateTime)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    platform_posts = db.relationship('PostPlatform', backref='post', lazy='dynamic', cascade='all, delete-orphan')

    def get_media_files(self):
        if self.media_files:
            return json.loads(self.media_files)
        return []

    def set_media_files(self, files: list):
        self.media_files = json.dumps(files)

    def get_thumbnail(self):
        files = self.get_media_files()
        return files[0] if files else None

    def __repr__(self):
        return f'<Post {self.id} {self.status}>'


class PostPlatform(db.Model):
    """Tracks per-platform publishing status of a post."""
    __tablename__ = 'post_platforms'

    id                  = db.Column(db.Integer, primary_key=True)
    post_id             = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    platform_account_id = db.Column(db.Integer, db.ForeignKey('platform_accounts.id'), nullable=False)
    platform            = db.Column(db.String(30))
    platform_post_id    = db.Column(db.String(255))   # ID returned by the platform after publishing
    status              = db.Column(db.String(30), default='pending')  # pending|published|failed
    error_message       = db.Column(db.Text)
    published_at        = db.Column(db.DateTime)

    # Relationships
    platform_account = db.relationship('PlatformAccount', backref='post_platforms')
    analytics        = db.relationship('PostAnalytics', backref='post_platform', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<PostPlatform {self.platform} {self.status}>'


class PostAnalytics(db.Model):
    """Daily analytics snapshot for a published post on a specific platform."""
    __tablename__ = 'post_analytics'

    id               = db.Column(db.Integer, primary_key=True)
    post_platform_id = db.Column(db.Integer, db.ForeignKey('post_platforms.id'), nullable=False)
    recorded_at      = db.Column(db.DateTime, default=datetime.utcnow)
    date             = db.Column(db.Date)
    views            = db.Column(db.Integer, default=0)
    likes            = db.Column(db.Integer, default=0)
    comments         = db.Column(db.Integer, default=0)
    shares           = db.Column(db.Integer, default=0)
    watch_time_secs  = db.Column(db.Integer, default=0)   # YouTube / TikTok
    reach            = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<PostAnalytics {self.date} views={self.views}>'
