"""Routes for connecting / disconnecting social media platform accounts."""
import secrets
from datetime import datetime, timedelta
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, session, current_app, jsonify)
from flask_login import login_required, current_user
from database.models import db, PlatformAccount
from services import get_service

platforms_bp = Blueprint('platforms', __name__)

PLATFORM_META = {
    'instagram': {'name': 'Instagram', 'icon': 'instagram', 'color': '#E1306C'},
    'tiktok':    {'name': 'TikTok',    'icon': 'tiktok',    'color': '#000000'},
    'facebook':  {'name': 'Facebook',  'icon': 'facebook',  'color': '#1877F2'},
    'youtube':   {'name': 'YouTube',   'icon': 'youtube',   'color': '#FF0000'},
}


@platforms_bp.route('/')
@login_required
def index():
    accounts = (PlatformAccount.query
                .filter_by(user_id=current_user.id, is_active=True)
                .order_by(PlatformAccount.connected_at.desc()).all())
    return render_template('platforms/connect.html',
                           accounts=accounts,
                           meta=PLATFORM_META)


@platforms_bp.route('/connect/<platform>')
@login_required
def connect(platform):
    if platform not in PLATFORM_META:
        flash('Platform tidak dikenal.', 'danger')
        return redirect(url_for('platforms.index'))

    state        = secrets.token_urlsafe(16)
    session['oauth_state']    = state
    session['oauth_platform'] = platform

    redirect_uri = url_for('platforms.callback', _external=True)

    try:
        svc     = get_service(platform, config=current_app.config)
        auth_url = svc.get_auth_url(redirect_uri, state)
        return redirect(auth_url)
    except Exception as e:
        flash(f'Gagal memulai OAuth: {str(e)}', 'danger')
        return redirect(url_for('platforms.index'))


@platforms_bp.route('/callback')
@login_required
def callback():
    state    = request.args.get('state')
    code     = request.args.get('code')
    error    = request.args.get('error')
    platform = session.pop('oauth_platform', None)

    if error:
        flash(f'OAuth ditolak: {error}', 'danger')
        return redirect(url_for('platforms.index'))

    if not code or state != session.pop('oauth_state', None):
        flash('OAuth gagal – state tidak valid.', 'danger')
        return redirect(url_for('platforms.index'))

    redirect_uri = url_for('platforms.callback', _external=True)

    try:
        svc       = get_service(platform, config=current_app.config)
        token_data = svc.exchange_code_for_token(code, redirect_uri)

        access_token  = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        expires_in    = token_data.get('expires_in', 3600)
        token_expiry  = datetime.utcnow() + timedelta(seconds=expires_in)

        # Create temp service with token to fetch profile
        tmp_account = PlatformAccount(
            user_id=current_user.id,
            platform=platform,
            access_token=access_token,
            refresh_token=refresh_token,
        )
        svc_with_token = get_service(platform, account=tmp_account, config=current_app.config)
        info           = svc_with_token.get_account_info()

        account_id   = info.get('id') or info.get('open_id') or ''
        account_name = (info.get('name') or info.get('display_name')
                        or info.get('username') or '')
        avatar_url   = (info.get('avatar_url') or info.get('profile_picture_url')
                        or info.get('picture', {}).get('data', {}).get('url') if isinstance(info.get('picture'), dict) else None
                        or '')

        # Upsert
        existing = PlatformAccount.query.filter_by(
            user_id=current_user.id, platform=platform, account_id=account_id
        ).first()
        if existing:
            account = existing
        else:
            account = PlatformAccount(user_id=current_user.id, platform=platform)
            db.session.add(account)

        account.account_id    = account_id
        account.account_name  = account_name
        account.avatar_url    = avatar_url
        account.access_token  = access_token
        account.refresh_token = refresh_token
        account.token_expiry  = token_expiry
        account.is_active     = True
        account.connected_at  = datetime.utcnow()
        db.session.commit()

        flash(f'✅ {PLATFORM_META[platform]["name"]} berhasil dihubungkan ({account_name}).', 'success')

    except Exception as e:
        flash(f'Gagal menghubungkan akun: {str(e)}', 'danger')

    return redirect(url_for('platforms.index'))


@platforms_bp.route('/disconnect/<int:account_id>', methods=['POST'])
@login_required
def disconnect(account_id):
    account = PlatformAccount.query.filter_by(
        id=account_id, user_id=current_user.id
    ).first_or_404()
    account.is_active = False
    db.session.commit()
    flash(f'Akun {account.account_name} ({account.platform}) telah diputus.', 'info')
    return redirect(url_for('platforms.index'))


@platforms_bp.route('/api/accounts')
@login_required
def api_accounts():
    accounts = PlatformAccount.query.filter_by(
        user_id=current_user.id, is_active=True
    ).all()
    return jsonify([{
        'id':           a.id,
        'platform':     a.platform,
        'account_name': a.account_name,
        'avatar_url':   a.avatar_url,
    } for a in accounts])
