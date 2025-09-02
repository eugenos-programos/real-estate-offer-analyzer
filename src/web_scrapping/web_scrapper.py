from abc import ABC, abstractmethod
from logging import Logger


class WebScrapper(ABC):
    site_url: str = None

    def __init__(self, site_url: str, logger: Logger):
        self.site_url = site_url
        self.logger = logger

    @abstractmethod
    def extract_offers(self):
        pass
