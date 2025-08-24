import time

import requests
from bs4 import BeautifulSoup

from .web_scrapper import WebScrapper


class KufarWebSrapper(WebScrapper):
    def __init__(self, logger):
        super().__init__(site_url="https://re.kufar.by", logger=logger)

    def _extract_offers_from_one_page(self, url: str) -> list:
        self.logger.info(f"Extracting offers for {url}")
        self._source = requests.request(method="POST", url=url)
        if self._source.status_code != 200:
            self.logger.error(f"Response code = {self._source.status_code}")
            return []
        self._soup = BeautifulSoup(markup=self._source.text, features="html.parser")
        offers_div = self._soup.find("div", class_="styles_cards__HMGBx")
        offers_hrefs = []
        for section in offers_div.find_all("section"):
            offers_hrefs.append(section.find_all("a", href=True)[0]["href"])
        return offers_hrefs

    def extract_offers(self) -> list[str]:
        offers = self._extract_offers_from_one_page(
            self.site_url + "/l/minsk/snyat/kvartiru"
        )
        next_page_url = self._soup.find(
            "a", href=True, attrs={"data-testid": "realty-pagination-next-link"}
        )
        while next_page_url is not None:
            offers += self._extract_offers_from_one_page(
                self.site_url + next_page_url["href"]
            )
            next_page_url = self._soup.find(
                "a", href=True, attrs={"data-testid": "realty-pagination-next-link"}
            )
        return offers

    def _extract_offer_info_label(
        self,
        offer_page_soup: BeautifulSoup,
        label_name: str,
        find_all_name: str = "span",
    ) -> str | None:
        try:
            data = (
                offer_page_soup.find("div", attrs={"data-name": label_name})
                .find_parent("div")
                .find_all(find_all_name)[-1]
                .get("data-name")
            )
            return data
        except (AttributeError, IndexError) as _:
            self.logger.warning(f"Cannot extract label {label_name}")
            return None

    def parse_offer_page(self, page_url: str) -> dict:
        page_source = None
        while page_source is None:
            try:
                page_source = requests.request(method="POST", url=page_url)
            except Exception as _:
                self.logger.warning(
                    f"Cannot extract page data from {page_url}. Retrying in 1 second"
                )
                time.sleep(1)
        if page_source.status_code != 200:
            self.logger.error(
                f"Cannot process page {page_url}. Code - {page_source.status_code}"
            )
            return {}
        page_bs = BeautifulSoup(markup=page_source.text, features="html.parser")

        offer_data = {}

        offer_data["id"] = page_url[page_url.rfind("/") + 1 :]

        offer_data["n_rooms"] = self._extract_offer_info_label(page_bs, "rooms", "a")
        offer_data["sq_meters_size"] = self._extract_offer_info_label(page_bs, "size")
        offer_data["bathroom_type"] = self._extract_offer_info_label(
            page_bs, "bathroom"
        )
        offer_data["balcony_type"] = self._extract_offer_info_label(page_bs, "balcony")
        offer_data["flat_improvement"] = self._extract_offer_info_label(
            page_bs, "flat_improvement"
        )
        offer_data["flat_bath"] = self._extract_offer_info_label(page_bs, "flat_bath")
        offer_data["flat_kitchen"] = self._extract_offer_info_label(
            page_bs, "flat_kitchen"
        )
        offer_data["flat_rent_for_whom"] = self._extract_offer_info_label(
            page_bs, "flat_rent_for_whom"
        )
        offer_data["flat_rent_prepayment"] = self._extract_offer_info_label(
            page_bs, "flat_rent_prepayment"
        )
        offer_data["flat_window_side"] = self._extract_offer_info_label(
            page_bs, "flat_windows_side"
        )
        offer_data["flat_condition"] = self._extract_offer_info_label(
            page_bs, "condition"
        )

        offer_data["building_number_floors"] = self._extract_offer_info_label(
            page_bs, "re_number_floors"
        )
        offer_data["year_built"] = self._extract_offer_info_label(page_bs, "year_built")
        offer_data["flat_building_improvements"] = self._extract_offer_info_label(
            page_bs, "flat_building_improvements"
        )
        offer_data["is_flat_new_building"] = self._extract_offer_info_label(
            page_bs, "flat_new_building"
        )

        offer_data["microdistrict"] = self._extract_offer_info_label(
            page_bs, "re_district", "a"
        )
        offer_data["metro"] = self._extract_offer_info_label(page_bs, "metro", "a")

        offer_data["flat_rent_couchettes"] = self._extract_offer_info_label(
            page_bs, "flat_rent_couchettes"
        )
        offer_data["is_studio"] = self._extract_offer_info_label(page_bs, "studio")
        offer_data["floor"] = self._extract_offer_info_label(page_bs, "floor")

        offer_data["description"] = str(
            page_bs.find("div", attrs={"id": "description"})
            .find("div", attrs={"itemprop": "description"})
            .contents[0]
        )

        offer_data["description"] += f"\n Ссылка на объявление - {page_url}."

        return offer_data
