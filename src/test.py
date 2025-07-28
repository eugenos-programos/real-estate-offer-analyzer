from qdrant_database.qdrant_database import QdrantDatabaseClient
from web_scrapping.kufar_web_scrapper import KufarWebSrapper

web_scrapper = KufarWebSrapper()
client = QdrantDatabaseClient(
    qdrant_localhost_port=6333,
    collection_name="real_estate_offers",
    vector_size=1028,
)


offers = web_scrapper.extract_offers()
print(f"Extracted {len(offers)} offers")

offers_data = []
for offer in offers:
    res = web_scrapper.parse_offer_page(offer)
    print(res)
    offers_data.append(res)
client.add_documents_to_database(offers_data)
