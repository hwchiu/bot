from urllib.parse import urlparse
from urllib.parse import urlunparse

import timeout_decorator
from loguru import logger

from .cloudscraper import CloudscraperLoader
from .httpx import HttpxLoader
from .loader import Loader
from .loader import LoaderError
from .pdf import PDFLoader
from .playwright import PlaywrightLoader
from .reel import ReelLoader
from .youtube import YoutubeLoader
from .ytdlp import YtdlpLoader

REPLACEMENTS = {
    "api.fxtwitter.com": [
        "twitter.com",
        "x.com",
        "fxtwitter.com",
        "vxtwitter.com",
        "fixvx.com",
        "twittpr.com",
        "fixupx.com",
    ]
}


def replace_domain(url: str) -> str:
    parsed = urlparse(url)
    for target, source in REPLACEMENTS.items():
        if parsed.netloc in source:
            fixed_url = parsed._replace(netloc=target)
            return urlunparse(fixed_url)
    return url


class URLLoader(Loader):
    def __init__(self) -> None:
        self.loaders: list[Loader] = [
            YoutubeLoader(),
            ReelLoader(),
            YtdlpLoader(),
            PDFLoader(),
            CloudscraperLoader(),
            HttpxLoader(),
            PlaywrightLoader(),
        ]

    @timeout_decorator.timeout(30)
    def load(self, url: str) -> str:
        url = replace_domain(url)

        for loader in self.loaders:
            try:
                result = loader.load(url)
                if result:
                    logger.info("[{}] Successfully loaded URL: {}", loader.__class__.__name__, url)
                    return result
                else:
                    logger.info("[{}] Failed to load URL: {}, got empty result", loader.__class__.__name__, url)
            except Exception as e:
                logger.info("[{}] Failed to load URL: {}, got error: {}", loader.__class__.__name__, url, e)

        raise LoaderError(f"Failed to load URL: {url}")
