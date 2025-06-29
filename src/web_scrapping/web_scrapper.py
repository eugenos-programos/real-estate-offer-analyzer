from abc import ABC, abstractmethod


class WebScrapper(ABC):
    site_url: str = None

    def __init__(self, site_url: str):
        self.site_url = site_url

    @abstractmethod
    def extract_offers(self):
        pass
