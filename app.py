"""Social Media Manager – main Flask application."""
import os
import logging
from dotenv import load_dotenv
load_dotenv()  
from flask import Flask, redirect, url_for
from flask_login import LoginManager
from database.models import db, User
from config import Config

logging.basicConfig(level=logging.INFO)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure required directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'data'), exist_ok=True)

    # ── Database ──────────────────────────────────────────────────────
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # ── Login manager ─────────────────────────────────────────────────
    login_manager = LoginManager(app)
    login_manager.login_view       = 'auth.login'
    login_manager.login_message    = 'Silakan login terlebih dahulu.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ── Blueprints ────────────────────────────────────────────────────
    from routes.auth      import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.platforms import platforms_bp
    from routes.content   import content_bp
    from routes.analytics import analytics_bp

    app.register_blueprint(auth_bp,       url_prefix='/auth')
    app.register_blueprint(dashboard_bp,  url_prefix='/dashboard')
    app.register_blueprint(platforms_bp,  url_prefix='/platforms')
    app.register_blueprint(content_bp,    url_prefix='/content')
    app.register_blueprint(analytics_bp,  url_prefix='/analytics')

    @app.route('/')
    def root():
        return redirect(url_for('dashboard.index'))

    # ── Scheduler ─────────────────────────────────────────────────────
    from apscheduler.schedulers.background import BackgroundScheduler
    from scheduler_worker import process_scheduled_posts, sync_analytics

    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(lambda: process_scheduled_posts(app), 'interval', minutes=1,
                      id='publish_posts')
    scheduler.add_job(lambda: sync_analytics(app), 'interval', hours=1,
                      id='sync_analytics')
    scheduler.start()

    # ── Template helpers ──────────────────────────────────────────────
    @app.template_filter('datetime_fmt')
    def datetime_fmt(value, fmt='%d %b %Y %H:%M'):
        if value is None:
            return '—'
        return value.strftime(fmt)

    @app.template_filter('platform_icon')
    def platform_icon(platform):
        icons = {
            'instagram': 'bi-instagram',
            'tiktok':    'bi-tiktok',
            'facebook':  'bi-facebook',
            'youtube':   'bi-youtube',
        }
        return icons.get(platform, 'bi-globe')

    @app.template_filter('platform_color')
    def platform_color(platform):
        colors = {
            'instagram': '#E1306C',
            'tiktok':    '#69C9D0',
            'facebook':  '#1877F2',
            'youtube':   '#FF0000',
        }
        return colors.get(platform, '#6c757d')

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
