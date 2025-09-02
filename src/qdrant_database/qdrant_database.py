import os
from logging import Logger

from langchain_core.documents import Document
from langchain_huggingface.embeddings import HuggingFaceEndpointEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, models


class QdrantDatabaseClient:
    def __init__(
        self,
        qdrant_localhost_port: str,
        collection_name: str,
        vector_size: int,
        logger: Logger,
        embeddings_model: str = "sentence-transformers/all-mpnet-base-v2",
    ):
        self._client = QdrantClient(
            host="localhost", port=qdrant_localhost_port, timeout=2.0
        )
        self.logger = logger
        if not self._client.collection_exists(collection_name):
            self._client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size, distance=models.Distance.COSINE
                ),
            )
        embeddings = HuggingFaceEndpointEmbeddings(
            model=embeddings_model,
            task="feature-extraction",
            huggingfacehub_api_token=os.environ.get("HUGGINGFACEHUB_API_TOKEN"),
        )
        self._vector_store = QdrantVectorStore(
            client=self._client, collection_name=collection_name, embedding=embeddings
        )
        self._collection_name = collection_name

    def _check_if_object_already_exists(self, obj_id: str) -> bool:
        scroll_res = self._client.scroll(
            collection_name=self._collection_name,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="id", match=models.MatchValue(value=obj_id)
                    )
                ]
            ),
        )
        return scroll_res[-1] is not None

    def add_documents_to_database(self, offers_data: list[dict]) -> None:
        documents = []
        for offer_data in offers_data:
            if not self._check_if_object_already_exists(offer_data["id"]):
                document = Document(
                    page_content=offer_data.pop("description")
                    if "description" in offer_data
                    else "",
                    metadata=offer_data,
                )
                documents.append(document)
                self.logger.info(
                    f"Object with id={offers_data['id']} added to vector store"
                )
            else:
                self.logger.warning(
                    f"Object with id={offer_data['id']} already exists in vector store"
                )
        self._vector_store.add_documents(documents)
        self.logger.info(f"Added {len(documents)} documents into Qdrant vector store.")

    def update_store(self, new_offers_data: list[dict]) -> None:
        pass

    def search_with_filters(self, query: str) -> list:
        docs = self._vector_store.similarity_search(query)
        return docs
