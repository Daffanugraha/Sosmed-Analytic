from flask import Blueprint, render_template
from flask_login import login_required, current_user
from database.models import Post, PlatformAccount, PostPlatform
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    user_id = current_user.id

    total_posts      = Post.query.filter_by(user_id=user_id).count()
    scheduled_posts  = Post.query.filter_by(user_id=user_id, status='scheduled').count()
    published_posts  = Post.query.filter_by(user_id=user_id, status='published').count()
    connected_accs   = PlatformAccount.query.filter_by(user_id=user_id, is_active=True).count()

    recent_posts = (Post.query
                    .filter_by(user_id=user_id)
                    .order_by(Post.created_at.desc())
                    .limit(5).all())

    upcoming = (Post.query
                .filter_by(user_id=user_id, status='scheduled')
                .filter(Post.scheduled_at >= datetime.utcnow())
                .order_by(Post.scheduled_at.asc())
                .limit(5).all())

    platforms = (PlatformAccount.query
                 .filter_by(user_id=user_id, is_active=True).all())

    return render_template('dashboard/index.html',
                           total_posts=total_posts,
                           scheduled_posts=scheduled_posts,
                           published_posts=published_posts,
                           connected_accs=connected_accs,
                           recent_posts=recent_posts,
                           upcoming=upcoming,
                           platforms=platforms)
