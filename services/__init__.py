from .instagram_service import InstagramService
from .tiktok_service    import TikTokService
from .facebook_service  import FacebookService
from .youtube_service   import YouTubeService

PLATFORM_SERVICES = {
    'instagram': InstagramService,
    'tiktok':    TikTokService,
    'facebook':  FacebookService,
    'youtube':   YouTubeService,
}

def get_service(platform: str, account=None, config=None):
    cls = PLATFORM_SERVICES.get(platform)
    if cls is None:
        raise ValueError(f"Unknown platform: {platform}")
    return cls(account=account, config=config or {})
