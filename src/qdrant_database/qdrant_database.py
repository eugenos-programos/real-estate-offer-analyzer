import os

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
        embeddings_model: str = "sentence-transformers/all-mpnet-base-v2",
    ):
        self._client = QdrantClient(
            host="localhost", port=qdrant_localhost_port, timeout=2.0
        )
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

    def add_documents_to_database(self, offers_data: list[dict]) -> None:
        documents = []
        for offer_data in offers_data:
            document = Document(
                page_content=offer_data["description"],
                metadata=offer_data.pop("description"),
            )
            documents.append(document)
        self._vector_store.add_documents(documents)

    def search_with_filters(self, query: str) -> list:
        docs = self._vector_store.similarity_search(query)
        return docs
