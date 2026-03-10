"""Routes for creating, scheduling and managing posts."""
import json
from datetime import datetime
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, jsonify, current_app)
from flask_login import login_required, current_user
from database.models import db, Post, PostPlatform, PlatformAccount
from utils.file_helper import save_uploaded_file, allowed_file, delete_file

content_bp = Blueprint('content', __name__)


@content_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    accounts = PlatformAccount.query.filter_by(
        user_id=current_user.id, is_active=True
    ).all()

    if request.method == 'POST':
        # ── Collect form fields ─────────────────────────────────────
        title         = request.form.get('title', '').strip()
        caption       = request.form.get('caption', '').strip()
        hashtags      = request.form.get('hashtags', '').strip()
        platform_ids  = request.form.getlist('platform_accounts')  # list of account ids
        schedule_type = request.form.get('schedule_type', 'now')   # now | schedule
        scheduled_str = request.form.get('scheduled_at', '')

        if not platform_ids:
            flash('Pilih minimal satu platform untuk publish.', 'danger')
            return render_template('content/upload.html', accounts=accounts)

        # ── Handle file uploads ──────────────────────────────────────
        files = request.files.getlist('media_files')
        files = [f for f in files if f and f.filename and allowed_file(f.filename)]

        if not files:
            flash('Upload minimal satu file media (video/gambar).', 'danger')
            return render_template('content/upload.html', accounts=accounts)

        saved_files = []
        media_type  = 'image'
        for f in files:
            meta = save_uploaded_file(f, current_user.id)
            saved_files.append(meta)
            if meta['media_type'] == 'video':
                media_type = 'video'

        # ── Determine schedule ───────────────────────────────────────
        scheduled_at = None
        status       = 'draft'
        if schedule_type == 'now':
            status       = 'scheduled'
            scheduled_at = datetime.utcnow()
        elif schedule_type == 'schedule' and scheduled_str:
            try:
                scheduled_at = datetime.strptime(scheduled_str, '%Y-%m-%dT%H:%M')
                status       = 'scheduled'
            except ValueError:
                flash('Format tanggal/jam tidak valid.', 'danger')
                return render_template('content/upload.html', accounts=accounts)

        # ── Create post record ───────────────────────────────────────
        post = Post(
            user_id    = current_user.id,
            title      = title,
            caption    = caption,
            hashtags   = hashtags,
            media_type = media_type,
            status     = status,
            scheduled_at = scheduled_at,
        )
        post.set_media_files([m['url'] for m in saved_files])
        db.session.add(post)
        db.session.flush()   # get post.id

        # ── Create per-platform records ──────────────────────────────
        for acc_id in platform_ids:
            acc = PlatformAccount.query.filter_by(
                id=acc_id, user_id=current_user.id, is_active=True
            ).first()
            if acc:
                pp = PostPlatform(
                    post_id             = post.id,
                    platform_account_id = acc.id,
                    platform            = acc.platform,
                    status              = 'pending',
                )
                db.session.add(pp)

        db.session.commit()

        if schedule_type == 'now':
            flash('✅ Post sedang diproses untuk publish!', 'success')
        else:
            flash(f'✅ Post dijadwalkan pada {scheduled_at.strftime("%d %b %Y %H:%M")}.', 'success')

        return redirect(url_for('content.posts'))

    return render_template('content/upload.html', accounts=accounts)


@content_bp.route('/posts')
@login_required
def posts():
    status_filter = request.args.get('status', 'all')
    query = Post.query.filter_by(user_id=current_user.id)
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    all_posts = query.order_by(Post.created_at.desc()).all()
    return render_template('content/posts.html', posts=all_posts,
                           status_filter=status_filter)


@content_bp.route('/posts/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first_or_404()
    for url in post.get_media_files():
        delete_file(url)
    db.session.delete(post)
    db.session.commit()
    flash('Post berhasil dihapus.', 'success')
    return redirect(url_for('content.posts'))


@content_bp.route('/posts/<int:post_id>')
@login_required
def post_detail(post_id):
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first_or_404()
    return jsonify({
        'id':          post.id,
        'title':       post.title,
        'caption':     post.caption,
        'status':      post.status,
        'scheduled_at': post.scheduled_at.isoformat() if post.scheduled_at else None,
        'published_at': post.published_at.isoformat() if post.published_at else None,
        'media_files': post.get_media_files(),
        'platforms':   [{
            'platform': pp.platform,
            'status':   pp.status,
            'error':    pp.error_message,
        } for pp in post.platform_posts.all()],
    })
