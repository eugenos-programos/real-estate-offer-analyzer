from dotenv import load_dotenv
from tqdm import tqdm

from logger.logger import get_logger_object
from qdrant_database.qdrant_database import QdrantDatabaseClient
from web_scrapping.kufar_web_scrapper import KufarWebSrapper

load_dotenv("../.env")
logger = get_logger_object()

web_scrapper = KufarWebSrapper(logger)
client = QdrantDatabaseClient(
    qdrant_localhost_port=8888,
    collection_name="real_estate_offers",
    vector_size=768,
)


offers = web_scrapper.extract_offers()
logger.info(f"Extracted {len(offers)} offers")

offers_data = []
for offer in tqdm(offers, desc="Processing real estate offers"):
    res = web_scrapper.parse_offer_page(offer)
    logger.info(f"Extracted data {res} for {offer}")
    offers_data.append(res)
client.add_documents_to_database(offers_data)
