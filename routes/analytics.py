"""Analytics routes – charts and post-performance data."""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from database.models import Post, PostPlatform, PostAnalytics, PlatformAccount
from datetime import date, timedelta
from sqlalchemy import func

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/')
@login_required
def index():
    accounts = PlatformAccount.query.filter_by(
        user_id=current_user.id, is_active=True
    ).all()
    published_posts = (Post.query
                       .filter_by(user_id=current_user.id, status='published')
                       .order_by(Post.published_at.desc()).all())
    return render_template('analytics/index.html',
                           accounts=accounts,
                           published_posts=published_posts)


@analytics_bp.route('/api/summary')
@login_required
def api_summary():
    """Overall totals across all posts."""
    pp_ids = [
        pp.id
        for post in Post.query.filter_by(user_id=current_user.id).all()
        for pp in post.platform_posts.all()
    ]
    totals = (PostAnalytics.query
              .filter(PostAnalytics.post_platform_id.in_(pp_ids))
              .with_entities(
                  func.sum(PostAnalytics.views).label('views'),
                  func.sum(PostAnalytics.likes).label('likes'),
                  func.sum(PostAnalytics.comments).label('comments'),
                  func.sum(PostAnalytics.shares).label('shares'),
              ).first())
    return jsonify({
        'views':    int(totals.views or 0),
        'likes':    int(totals.likes or 0),
        'comments': int(totals.comments or 0),
        'shares':   int(totals.shares or 0),
    })


@analytics_bp.route('/api/post/<int:post_id>')
@login_required
def api_post_analytics(post_id):
    """Per-day analytics for all platforms of a specific post."""
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first_or_404()
    days = int(request.args.get('days', 30))
    since = date.today() - timedelta(days=days)

    result = {}
    for pp in post.platform_posts.all():
        records = (PostAnalytics.query
                   .filter(PostAnalytics.post_platform_id == pp.id,
                           PostAnalytics.date >= since)
                   .order_by(PostAnalytics.date).all())
        result[pp.platform] = {
            'labels': [str(r.date) for r in records],
            'views':  [r.views    for r in records],
            'likes':  [r.likes    for r in records],
            'comments': [r.comments for r in records],
            'shares':   [r.shares   for r in records],
        }
    return jsonify(result)


@analytics_bp.route('/api/platform/<int:account_id>')
@login_required
def api_platform_analytics(account_id):
    """Aggregate daily analytics for all posts of a specific platform account."""
    account = PlatformAccount.query.filter_by(
        id=account_id, user_id=current_user.id
    ).first_or_404()
    days  = int(request.args.get('days', 30))
    since = date.today() - timedelta(days=days)

    pp_ids = [pp.id for pp in account.post_platforms
              if pp.post.user_id == current_user.id]

    records = (PostAnalytics.query
               .filter(PostAnalytics.post_platform_id.in_(pp_ids),
                       PostAnalytics.date >= since)
               .order_by(PostAnalytics.date).all())

    # Group by date
    from collections import defaultdict
    daily = defaultdict(lambda: {'views': 0, 'likes': 0, 'comments': 0, 'shares': 0})
    for r in records:
        d = str(r.date)
        daily[d]['views']    += r.views
        daily[d]['likes']    += r.likes
        daily[d]['comments'] += r.comments
        daily[d]['shares']   += r.shares

    labels = sorted(daily.keys())
    return jsonify({
        'labels':   labels,
        'views':    [daily[l]['views']    for l in labels],
        'likes':    [daily[l]['likes']    for l in labels],
        'comments': [daily[l]['comments'] for l in labels],
        'shares':   [daily[l]['shares']   for l in labels],
    })
