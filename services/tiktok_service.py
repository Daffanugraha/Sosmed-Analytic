"""TikTok for Developers API integration.

Uses TikTok Login Kit (OAuth 2.0) and Content Posting API.
Developer portal: https://developers.tiktok.com/
"""
import requests
from urllib.parse import urlencode
from .base_service import BasePlatformService


class TikTokService(BasePlatformService):
    PLATFORM   = 'tiktok'
    AUTH_URL   = 'https://www.tiktok.com/v2/auth/authorize/'
    TOKEN_URL  = 'https://open.tiktokapis.com/v2/oauth/token/'
    API_BASE   = 'https://open.tiktokapis.com/v2'

    def __init__(self, account=None, config=None):
        super().__init__(account, config)
        self.client_key    = config.get('TIKTOK_CLIENT_KEY', '')
        self.client_secret = config.get('TIKTOK_CLIENT_SECRET', '')

    # ── OAuth ──────────────────────────────────────────────────────────
    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        params = {
            'client_key':    self.client_key,
            'redirect_uri':  redirect_uri,
            'scope':         'user.info.basic,video.upload,video.list',
            'response_type': 'code',
            'state':         state,
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> dict:
        r = requests.post(self.TOKEN_URL, data={
            'client_key':    self.client_key,
            'client_secret': self.client_secret,
            'code':          code,
            'grant_type':    'authorization_code',
            'redirect_uri':  redirect_uri,
        }, headers={'Content-Type': 'application/x-www-form-urlencoded'},
           timeout=30)
        r.raise_for_status()
        return r.json().get('data', {})

    def refresh_access_token(self) -> dict:
        r = requests.post(self.TOKEN_URL, data={
            'client_key':     self.client_key,
            'client_secret':  self.client_secret,
            'grant_type':     'refresh_token',
            'refresh_token':  self.account.refresh_token,
        }, headers={'Content-Type': 'application/x-www-form-urlencoded'},
           timeout=30)
        r.raise_for_status()
        return r.json().get('data', {})

    def get_account_info(self) -> dict:
        r = requests.get(
            f"{self.API_BASE}/user/info/",
            params={'fields': 'open_id,union_id,avatar_url,display_name'},
            headers={'Authorization': f'Bearer {self.access_token}'},
            timeout=30)
        r.raise_for_status()
        return r.json().get('data', {}).get('user', {})

    # ── Publishing ─────────────────────────────────────────────────────
    def publish_post(self, post, media_path: str) -> dict:
        """TikTok uses an 'init → chunk upload → publish' flow."""
        try:
            file_size = 0
            try:
                import os
                file_size = os.path.getsize(media_path)
            except Exception:
                pass

            # 1. Init upload
            init_r = requests.post(
                f"{self.API_BASE}/post/publish/video/init/",
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type':  'application/json; charset=UTF-8',
                },
                json={
                    'post_info': {
                        'title':            post.caption or '',
                        'privacy_level':    'PUBLIC_TO_EVERYONE',
                        'disable_duet':     False,
                        'disable_comment':  False,
                        'disable_stitch':   False,
                        'video_cover_timestamp_ms': 1000,
                    },
                    'source_info': {
                        'source':          'FILE_UPLOAD',
                        'video_size':       file_size,
                        'chunk_size':       file_size,
                        'total_chunk_count': 1,
                    },
                }, timeout=30)
            init_r.raise_for_status()
            init_data    = init_r.json().get('data', {})
            publish_id   = init_data.get('publish_id')
            upload_url   = init_data.get('upload_url')

            # 2. Upload video chunk
            with open(media_path, 'rb') as f:
                video_data = f.read()
            up_r = requests.put(
                upload_url,
                data=video_data,
                headers={
                    'Content-Range': f'bytes 0-{file_size - 1}/{file_size}',
                    'Content-Type':  'video/mp4',
                }, timeout=120)
            up_r.raise_for_status()

            return {'success': True, 'platform_post_id': publish_id}
        except Exception as e:
            return {'success': False, 'platform_post_id': None, 'error': str(e)}

    # ── Analytics ──────────────────────────────────────────────────────
    def fetch_analytics(self, platform_post_id: str) -> dict:
        try:
            r = requests.post(
                f"{self.API_BASE}/video/query/",
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type':  'application/json',
                },
                json={
                    'filters':   {'video_ids': [platform_post_id]},
                    'fields':    ['id', 'like_count', 'comment_count',
                                  'share_count', 'view_count'],
                    'max_count': 1,
                }, timeout=30)
            r.raise_for_status()
            data = r.json().get('data', {}).get('videos', [{}])[0]
            return {
                'views':    data.get('view_count', 0),
                'likes':    data.get('like_count', 0),
                'comments': data.get('comment_count', 0),
                'shares':   data.get('share_count', 0),
                'reach':    data.get('view_count', 0),
            }
        except Exception:
            return {'views': 0, 'likes': 0, 'comments': 0, 'shares': 0, 'reach': 0}
