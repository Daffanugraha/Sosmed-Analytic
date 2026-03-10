"""Background scheduler – runs every minute to publish due posts."""
from datetime import datetime, timezone
import logging

log = logging.getLogger(__name__)


def process_scheduled_posts(app):
    with app.app_context():
        from database.models import db, Post, PostPlatform, PostAnalytics
        from services import get_service
        import json, os

        now = datetime.utcnow()
        due_posts = Post.query.filter(
            Post.status == 'scheduled',
            Post.scheduled_at <= now,
        ).all()

        for post in due_posts:
            post.status = 'publishing'
            db.session.commit()

            all_ok   = True
            any_done = False
            media_files = post.get_media_files()
            primary_media = media_files[0] if media_files else None

            for pp in post.platform_posts.filter_by(status='pending').all():
                account = pp.platform_account
                if not account or not account.is_active:
                    pp.status = 'failed'
                    pp.error_message = 'Account not connected'
                    all_ok = False
                    continue

                try:
                    svc = get_service(
                        account.platform,
                        account=account,
                        config=app.config,
                    )
                    # Resolve file path from URL
                    media_path = None
                    if primary_media:
                        media_path = os.path.join(
                            app.static_folder,
                            primary_media.lstrip('/static/').lstrip('static/'),
                        )

                    result = svc.publish_post(post, media_path)

                    if result.get('success'):
                        pp.status           = 'published'
                        pp.platform_post_id = result.get('platform_post_id')
                        pp.published_at     = datetime.utcnow()
                        any_done = True
                    else:
                        pp.status        = 'failed'
                        pp.error_message = result.get('error', 'Unknown error')
                        all_ok = False

                except Exception as e:
                    pp.status        = 'failed'
                    pp.error_message = str(e)
                    all_ok = False
                    log.exception("Publish error post=%s platform=%s", post.id, account.platform)

            post.status = 'published' if any_done else ('failed' if not all_ok else 'published')
            if any_done:
                post.published_at = datetime.utcnow()
            db.session.commit()


def sync_analytics(app):
    """Fetch latest analytics for recently published posts."""
    with app.app_context():
        from database.models import db, PostPlatform, PostAnalytics
        from services import get_service
        from datetime import date

        published = PostPlatform.query.filter_by(status='published').all()
        today = date.today()

        for pp in published:
            if not pp.platform_post_id:
                continue
            account = pp.platform_account
            if not account or not account.is_active:
                continue
            try:
                svc    = get_service(account.platform, account=account, config=app.config)
                data   = svc.fetch_analytics(pp.platform_post_id)
                record = PostAnalytics.query.filter_by(
                    post_platform_id=pp.id, date=today).first()
                if not record:
                    record = PostAnalytics(post_platform_id=pp.id, date=today)
                    db.session.add(record)
                record.views           = data.get('views', 0)
                record.likes           = data.get('likes', 0)
                record.comments        = data.get('comments', 0)
                record.shares          = data.get('shares', 0)
                record.reach           = data.get('reach', 0)
                record.watch_time_secs = data.get('watch_time_secs', 0)
                db.session.commit()
            except Exception as e:
                log.warning("Analytics sync error pp=%s: %s", pp.id, e)
