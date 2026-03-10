"""Facebook Graph API integration.

Supports posting to Facebook Pages (not personal profiles).
Developer portal: https://developers.facebook.com/
"""
import requests
from urllib.parse import urlencode
from .base_service import BasePlatformService


class FacebookService(BasePlatformService):
    PLATFORM  = 'facebook'
    AUTH_URL  = 'https://www.facebook.com/v18.0/dialog/oauth'
    TOKEN_URL = 'https://graph.facebook.com/v18.0/oauth/access_token'
    GRAPH_URL = 'https://graph.facebook.com/v18.0'

    def __init__(self, account=None, config=None):
        super().__init__(account, config)
        self.client_id     = config.get('FACEBOOK_CLIENT_ID', '')
        self.client_secret = config.get('FACEBOOK_CLIENT_SECRET', '')

    # ── OAuth ──────────────────────────────────────────────────────────
    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        params = {
            'client_id':     self.client_id,
            'redirect_uri':  redirect_uri,
            'scope':         'pages_show_list,pages_read_engagement,pages_manage_posts,'
                             'pages_manage_engagement,read_insights,publish_video',
            'response_type': 'code',
            'state':         state,
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> dict:
        r = requests.get(self.TOKEN_URL, params={
            'client_id':     self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri':  redirect_uri,
            'code':          code,
        }, timeout=30)
        r.raise_for_status()
        return r.json()   # {access_token, token_type, expires_in}

    def get_pages(self) -> list:
        """List Facebook Pages the user manages."""
        r = requests.get(f"{self.GRAPH_URL}/me/accounts", params={
            'access_token': self.access_token,
        }, timeout=30)
        r.raise_for_status()
        return r.json().get('data', [])

    def get_account_info(self) -> dict:
        r = requests.get(f"{self.GRAPH_URL}/me", params={
            'fields':       'id,name,email,picture',
            'access_token': self.access_token,
        }, timeout=30)
        r.raise_for_status()
        return r.json()

    # ── Publishing ─────────────────────────────────────────────────────
    def publish_post(self, post, media_path: str) -> dict:
        try:
            page_id    = self.account.account_id
            extra      = self.account.get_extra_data()
            page_token = extra.get('page_token', self.access_token)

            if post.media_type == 'video':
                url = f"{self.GRAPH_URL}/{page_id}/videos"
                with open(media_path, 'rb') as f:
                    r = requests.post(url, params={'access_token': page_token},
                                      data={'description': post.caption or ''},
                                      files={'source': f}, timeout=120)
            else:
                url = f"{self.GRAPH_URL}/{page_id}/photos"
                with open(media_path, 'rb') as f:
                    r = requests.post(url, params={'access_token': page_token},
                                      data={'caption': post.caption or ''},
                                      files={'source': f}, timeout=60)
            r.raise_for_status()
            return {'success': True, 'platform_post_id': r.json().get('id')}
        except Exception as e:
            return {'success': False, 'platform_post_id': None, 'error': str(e)}

    # ── Analytics ──────────────────────────────────────────────────────
    def fetch_analytics(self, platform_post_id: str) -> dict:
        try:
            extra      = self.account.get_extra_data() if self.account else {}
            page_token = extra.get('page_token', self.access_token)
            r = requests.get(
                f"{self.GRAPH_URL}/{platform_post_id}/insights",
                params={
                    'metric':       'post_impressions,post_reactions_by_type_total,'
                                    'post_clicks,post_shares',
                    'access_token': page_token,
                }, timeout=30)
            r.raise_for_status()
            metrics = {item['name']: item['values'][-1]['value']
                       for item in r.json().get('data', [])}
            reactions = metrics.get('post_reactions_by_type_total', {})
            likes = sum(reactions.values()) if isinstance(reactions, dict) else 0
            return {
                'views':    metrics.get('post_impressions', 0),
                'likes':    likes,
                'comments': 0,
                'shares':   metrics.get('post_shares', {}).get('count', 0)
                            if isinstance(metrics.get('post_shares'), dict) else 0,
                'reach':    metrics.get('post_impressions', 0),
            }
        except Exception:
            return {'views': 0, 'likes': 0, 'comments': 0, 'shares': 0, 'reach': 0}
