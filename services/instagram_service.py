"""Instagram Graph API integration.

Requires a Facebook App with Instagram Basic Display or
Instagram Graph API access (Business/Creator accounts).
"""
import requests
from urllib.parse import urlencode
from .base_service import BasePlatformService


class InstagramService(BasePlatformService):
    PLATFORM = 'instagram'
    AUTH_URL       = 'https://www.facebook.com/v18.0/dialog/oauth'
    TOKEN_URL      = 'https://graph.facebook.com/v18.0/oauth/access_token'
    LONG_TOKEN_URL = 'https://graph.facebook.com/v18.0/oauth/access_token'
    GRAPH_URL      = 'https://graph.facebook.com/v18.0' # Changed from graph.instagram.com

    def __init__(self, account=None, config=None):
        super().__init__(account, config)
        self.client_id     = config.get('INSTAGRAM_CLIENT_ID', '')
        self.client_secret = config.get('INSTAGRAM_CLIENT_SECRET', '')

    # ── OAuth ──────────────────────────────────────────────────────────
    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        params = {
            'client_id':     self.client_id,
            'redirect_uri':  redirect_uri,
            'scope':         'user_profile,user_media',
            'response_type': 'code',
            'state':         state,
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> dict:
        # 1. Get short-lived token
        r = requests.get(self.TOKEN_URL, params={
            'client_id':     self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri':  redirect_uri,
            'code':          code,
        }, timeout=30)
        r.raise_for_status()
        data = r.json()

        # 2. Exchange for long-lived token
        lr = requests.get(self.LONG_TOKEN_URL, params={
            'grant_type':        'fb_exchange_token', # Changed from ig_exchange_token
            'client_id':         self.client_id,
            'client_secret':     self.client_secret,
            'fb_exchange_token': data['access_token'],
        }, timeout=30)
        lr.raise_for_status()
        return lr.json()

    def get_account_info(self) -> dict:
        r = requests.get(f"{self.GRAPH_URL}/me", params={
            'fields':       'id,username,name,profile_picture_url,account_type',
            'access_token': self.access_token,
        }, timeout=30)
        r.raise_for_status()
        return r.json()

    # ── Publishing ─────────────────────────────────────────────────────
    def publish_post(self, post, media_path: str) -> dict:
        """Upload via container → publish two-step flow."""
        try:
            ig_user_id = self.account.account_id
            media_type = post.media_type

            if media_type == 'video':
                # Step 1 – create video container
                r = requests.post(
                    f"{self.GRAPH_URL}/{ig_user_id}/media",
                    params={'access_token': self.access_token},
                    data={
                        'media_type': 'REELS',
                        'video_url':  media_path,   # must be public URL
                        'caption':    post.caption or '',
                    }, timeout=60)
            else:
                r = requests.post(
                    f"{self.GRAPH_URL}/{ig_user_id}/media",
                    params={'access_token': self.access_token},
                    data={
                        'image_url': media_path,
                        'caption':   post.caption or '',
                    }, timeout=60)

            r.raise_for_status()
            container_id = r.json().get('id')

            # Step 2 – publish the container
            pub = requests.post(
                f"{self.GRAPH_URL}/{ig_user_id}/media_publish",
                params={'access_token': self.access_token},
                data={'creation_id': container_id},
                timeout=30)
            pub.raise_for_status()
            return {'success': True, 'platform_post_id': pub.json().get('id')}

        except Exception as e:
            return {'success': False, 'platform_post_id': None, 'error': str(e)}

    # ── Analytics ──────────────────────────────────────────────────────
    def fetch_analytics(self, platform_post_id: str) -> dict:
        try:
            r = requests.get(
                f"{self.GRAPH_URL}/{platform_post_id}/insights",
                params={
                    'metric':       'impressions,reach,likes,comments,shares,saved',
                    'access_token': self.access_token,
                }, timeout=30)
            r.raise_for_status()
            metrics = {item['name']: item['values'][0]['value']
                       for item in r.json().get('data', [])}
            return {
                'views':    metrics.get('impressions', 0),
                'reach':    metrics.get('reach', 0),
                'likes':    metrics.get('likes', 0),
                'comments': metrics.get('comments', 0),
                'shares':   metrics.get('shares', 0),
            }
        except Exception:
            return {'views': 0, 'likes': 0, 'comments': 0, 'shares': 0, 'reach': 0}
