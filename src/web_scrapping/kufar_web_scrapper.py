from .web_scrapper import WebScrapper
from bs4 import BeautifulSoup
import requests


class KufarWebSrapper(WebScrapper):
    def __init__(self):
        super().__init__(site_url="https://re.kufar.by")

    def _extract_offers_from_one_page(self, url: str) -> list:
        print(url)
        self._source = requests.request(method='POST', url=url)
        if self._source.status_code != 200:
            print(f"Response code = {self._source.status_code}")
            return []
        self._soup = BeautifulSoup(
            markup=self._source.text,
            features='html.parser'
        )
        offers_div = self._soup.find('div', class_='styles_cards__HMGBx')
        offers_hrefs = []
        for section in offers_div.find_all('section'):
            offers_hrefs.append(section.find_all('a', href=True)[0]['href'])
        return offers_hrefs


    def extract_offers(self) -> list[str]:
        offers = self._extract_offers_from_one_page(self.site_url + "/l/minsk/snyat/kvartiru")
        next_page_url = self._soup.find('a', href=True, attrs={'data-testid': 'realty-pagination-next-link'})
        while next_page_url is not None:
            offers += self._extract_offers_from_one_page(self.site_url + next_page_url['href'])
            next_page_url = self._soup.find('a', href=True, attrs={'data-testid': 'realty-pagination-next-link'})
        return offers
    