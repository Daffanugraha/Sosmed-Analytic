"""Base class for all social media platform services."""
import requests
from datetime import datetime


class BasePlatformService:
    PLATFORM = 'base'

    def __init__(self, account=None, config=None):
        self.account = account
        self.config = config or {}
        self.access_token = account.access_token if account else None

    # ──────────────────────────────────────────────────────────────────
    # OAuth helpers  (must be implemented per platform)
    # ──────────────────────────────────────────────────────────────────
    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        raise NotImplementedError

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> dict:
        raise NotImplementedError

    def refresh_access_token(self) -> dict:
        raise NotImplementedError

    def get_account_info(self) -> dict:
        raise NotImplementedError

    # ──────────────────────────────────────────────────────────────────
    # Publishing
    # ──────────────────────────────────────────────────────────────────
    def publish_post(self, post, media_path: str) -> dict:
        """
        Publish a post. Returns dict with keys:
          success: bool
          platform_post_id: str | None
          error: str | None
        """
        raise NotImplementedError

    # ──────────────────────────────────────────────────────────────────
    # Analytics
    # ──────────────────────────────────────────────────────────────────
    def fetch_analytics(self, platform_post_id: str) -> dict:
        """
        Fetch analytics for a published post. Returns dict:
          views, likes, comments, shares, watch_time_secs, reach
        """
        raise NotImplementedError

    # ──────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────
    def _get(self, url, params=None):
        params = params or {}
        params['access_token'] = self.access_token
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def _post(self, url, data=None, json=None, files=None):
        headers = {}
        if not files:
            headers['Content-Type'] = 'application/json'
        r = requests.post(url, data=data, json=json, files=files,
                          headers=headers if not files else {}, timeout=60)
        r.raise_for_status()
        return r.json()
