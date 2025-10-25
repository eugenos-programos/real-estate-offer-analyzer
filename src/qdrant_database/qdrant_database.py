import json
import os
from logging import Logger

from huggingface_hub import InferenceClient
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
        embeddings_model: str = "Qwen/Qwen3-Embedding-8B",
        query_maker_model: str = "Qwen/Qwen2.5-VL-7B-Instruct",
        prompt_for_query_maker_moodel_template_filepath: str = "prompt_template.txt",
    ):
        self.logger = logger
        self._client = QdrantClient(
            host="localhost", port=qdrant_localhost_port, timeout=2.0
        )

        # check connection
        try:
            self._client.get_collections()
        except Exception:
            self.logger.fatal(
                "Cannot extract collections from Qdrant DB. Please check connection."
            )
            exit(1)
        if not self._client.collection_exists(collection_name):
            self._client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size, distance=models.Distance.COSINE
                ),
            )
        with open(
            prompt_for_query_maker_moodel_template_filepath, "r", encoding="utf8"
        ) as fp:
            self._prompt_template = fp.read()
        embeddings = HuggingFaceEndpointEmbeddings(
            model=embeddings_model,
            task="feature-extraction",
            huggingfacehub_api_token=os.environ.get("HUGGINGFACEHUB_API_TOKEN"),
        )
        self._embed_model = embeddings
        self._query_maker_model = InferenceClient(
            model=query_maker_model,
            provider="hyperbolic",
            api_key=os.environ.get("HUGGINGFACEHUB_API_TOKEN"),
        )
        self._vector_store = QdrantVectorStore(
            client=self._client,
            collection_name=collection_name,
            embedding=self._embed_model,
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
                    f"Object with id={offer_data['id']} added to vector store"
                )
            else:
                self.logger.warning(
                    f"Object with id={offer_data['id']} already exists in vector store"
                )
        self._vector_store.add_documents(documents)
        self.logger.info(f"Added {len(documents)} documents into Qdrant vector store.")

    def update_store(self, new_offers_data: list[dict]) -> None:
        pass

    @staticmethod
    def _convert_query_dict_to_qdrant_filters(
        query_dict: dict,
    ) -> list[models.FieldCondition]:
        qdrant_field_conditions = []
        for key in query_dict:
            if query_dict[key] == "Не известно":
                continue
            elif "От" in query_dict[key]:
                qdrant_field_conditions.append(
                    models.FieldCondition(
                        key=key,
                        range=models.Range(
                            gte=query_dict[key]
                        ),  # TODO: check if correct
                    )
                )
            elif "До" in query_dict[key]:
                qdrant_field_conditions.append(
                    models.FieldCondition(
                        key=key,
                        range=models.Range(lte=query_dict[key]),  # TODO: check if works
                    )
                )
            elif "," in query_dict[key]:
                continue
                qdrant_field_conditions.append(
                    models.FieldCondition(
                        key=key, match=models.MatchAny(any=query_dict[key].split(","))
                    )
                )
            else:
                qdrant_field_conditions.append(
                    models.FieldCondition(
                        key=key, match=models.MatchValue(value=query_dict[key])
                    )
                )
        return qdrant_field_conditions

    def search(self, query: str) -> list:
        messages = [
            {
                "role": "user",
                "content": [{"type": "text", "text": self._prompt_template % query}],
            }
        ]
        print(self._prompt_template % query)
        completion = self._query_maker_model.chat.completions.create(
            model="Qwen/Qwen2.5-VL-7B-Instruct", messages=messages, temperature=0.1
        )
        out = completion.choices[0].message.content
        query_dict = json.loads(out[out.rfind("{") : out.rfind("}") + 1])
        qdrant_filters = self._convert_query_dict_to_qdrant_filters(query_dict)
        print(qdrant_filters)
        docs = self._client.scroll(
            collection_name=self._collection_name,
            scroll_filter=models.Filter(must=qdrant_filters),
        )
        return docs
