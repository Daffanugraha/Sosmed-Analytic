"""YouTube Data API v3 integration (Google OAuth 2.0).

Videos → YouTube channel, Images → Community posts (channel must be eligible).
Developer portal: https://console.cloud.google.com/
"""
import requests
from urllib.parse import urlencode
from .base_service import BasePlatformService


SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/yt-analytics.readonly',
]


class YouTubeService(BasePlatformService):
    PLATFORM  = 'youtube'
    AUTH_URL  = 'https://accounts.google.com/o/oauth2/v2/auth'
    TOKEN_URL = 'https://oauth2.googleapis.com/token'
    API_BASE  = 'https://www.googleapis.com/youtube/v3'
    UPLOAD_URL = 'https://www.googleapis.com/upload/youtube/v3/videos'

    def __init__(self, account=None, config=None):
        super().__init__(account, config)
        self.client_id     = config.get('YOUTUBE_CLIENT_ID', '')
        self.client_secret = config.get('YOUTUBE_CLIENT_SECRET', '')

    # ── OAuth ──────────────────────────────────────────────────────────
    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        params = {
            'client_id':             self.client_id,
            'redirect_uri':          redirect_uri,
            'scope':                 ' '.join(SCOPES),
            'response_type':         'code',
            'state':                 state,
            'access_type':           'offline',
            'prompt':                'consent',
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> dict:
        r = requests.post(self.TOKEN_URL, data={
            'client_id':     self.client_id,
            'client_secret': self.client_secret,
            'code':          code,
            'grant_type':    'authorization_code',
            'redirect_uri':  redirect_uri,
        }, timeout=30)
        r.raise_for_status()
        return r.json()  # {access_token, refresh_token, expires_in, token_type}

    def refresh_access_token(self) -> dict:
        r = requests.post(self.TOKEN_URL, data={
            'client_id':     self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.account.refresh_token,
            'grant_type':    'refresh_token',
        }, timeout=30)
        r.raise_for_status()
        return r.json()

    def get_account_info(self) -> dict:
        r = requests.get(f"{self.API_BASE}/channels", params={
            'part':  'snippet,statistics',
            'mine':  'true',
        }, headers={'Authorization': f'Bearer {self.access_token}'}, timeout=30)
        r.raise_for_status()
        items = r.json().get('items', [])
        if items:
            ch = items[0]
            return {
                'id':        ch['id'],
                'name':      ch['snippet']['title'],
                'avatar':    ch['snippet']['thumbnails'].get('default', {}).get('url'),
                'subs':      ch['statistics'].get('subscriberCount', 0),
            }
        return {}

    # ── Publishing ─────────────────────────────────────────────────────
    def publish_post(self, post, media_path: str) -> dict:
        """
        Videos → upload as YouTube video.
        Images → Community post (text-only fallback if not eligible).
        """
        try:
            if post.media_type == 'video':
                return self._upload_video(post, media_path)
            else:
                return self._create_community_post(post, media_path)
        except Exception as e:
            return {'success': False, 'platform_post_id': None, 'error': str(e)}

    def _upload_video(self, post, media_path: str) -> dict:
        import os
        file_size = os.path.getsize(media_path)
        title     = post.title or (post.caption[:100] if post.caption else 'Untitled')
        # 1 – initiate resumable upload
        init_r = requests.post(
            self.UPLOAD_URL,
            params={'uploadType': 'resumable', 'part': 'snippet,status'},
            headers={
                'Authorization':         f'Bearer {self.access_token}',
                'Content-Type':          'application/json',
                'X-Upload-Content-Type': 'video/mp4',
                'X-Upload-Content-Length': str(file_size),
            },
            json={
                'snippet': {
                    'title':       title,
                    'description': post.caption or '',
                    'tags':        (post.hashtags or '').split(),
                },
                'status': {'privacyStatus': 'public'},
            }, timeout=30)
        init_r.raise_for_status()
        upload_url = init_r.headers.get('Location')

        # 2 – upload file
        with open(media_path, 'rb') as f:
            up_r = requests.put(
                upload_url,
                data=f,
                headers={
                    'Content-Length': str(file_size),
                    'Content-Type':   'video/mp4',
                }, timeout=300)
        up_r.raise_for_status()
        video_id = up_r.json().get('id')
        return {'success': True, 'platform_post_id': video_id}

    def _create_community_post(self, post, media_path: str) -> dict:
        # Community posts require eligible channels; fallback: post as text
        r = requests.post(
            f"{self.API_BASE}/communityPosts",
            headers={'Authorization': f'Bearer {self.access_token}',
                     'Content-Type':  'application/json'},
            json={'snippet': {'type': 'textPost',
                              'textOriginalContent': post.caption or ''}},
            timeout=30)
        r.raise_for_status()
        return {'success': True, 'platform_post_id': r.json().get('id')}

    # ── Analytics ──────────────────────────────────────────────────────
    def fetch_analytics(self, platform_post_id: str) -> dict:
        try:
            from datetime import date, timedelta
            end   = date.today().isoformat()
            start = (date.today() - timedelta(days=30)).isoformat()
            r = requests.get(
                'https://youtubeanalytics.googleapis.com/v2/reports',
                params={
                    'ids':        'channel==MINE',
                    'startDate':  start,
                    'endDate':    end,
                    'metrics':    'views,likes,comments,estimatedMinutesWatched',
                    'filters':    f'video=={platform_post_id}',
                    'dimensions': 'day',
                },
                headers={'Authorization': f'Bearer {self.access_token}'},
                timeout=30)
            r.raise_for_status()
            rows = r.json().get('rows', [])
            totals = [sum(row[i] for row in rows) for i in range(1, 5)]
            return {
                'views':           int(totals[0]) if totals else 0,
                'likes':           int(totals[1]) if len(totals) > 1 else 0,
                'comments':        int(totals[2]) if len(totals) > 2 else 0,
                'watch_time_secs': int(totals[3] * 60) if len(totals) > 3 else 0,
                'shares':          0,
                'reach':           int(totals[0]) if totals else 0,
            }
        except Exception:
            return {'views': 0, 'likes': 0, 'comments': 0, 'shares': 0,
                    'watch_time_secs': 0, 'reach': 0}
