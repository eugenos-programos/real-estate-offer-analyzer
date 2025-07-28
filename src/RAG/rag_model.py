import torch
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain.llms.huggingface_pipeline import HuggingFacePipeline
from langchain.prompts import PromptTemplate
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline


class RAG:
    def __init__(self, embedder: HuggingFaceInferenceAPIEmbeddings, qdrant_client):
        self.embedder = embedder
        self.qdrant_client = qdrant_client

        model_name = "mistralai/Mistral-7B-Instruct-v0.1"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name, device_map="auto", torch_dtype=torch.float16
        )

        pipe = pipeline(
            "text-generation", model=model, tokenizer=tokenizer, max_new_tokens=256
        )

        self._prompt_template = PromptTemplate(
            template="""
                <s>[INST] Ты помощник по выбору предложений об аренде недвижимости.
                        Сформируй ответ на осное приведённого контекста об релевантных предложениях и вопроса.
    
                Контект:
                {context}
    
                Вопрос: {question}
                
                Ответ: [/INST]""",
            input_variables=["context", "question"],
        )

        self._qa_chain = RetrievalQA.from_chain_type(
            llm=HuggingFacePipeline(pipeline=pipe),
            chain_type="stuff",
            retriever=self.qdrant_client.as_retriever(),
            return_source_documents=True,
            chain_type_kwargs={"prompt": self._prompt_template},
        )

    def __call__(self, query: str):
        result = self._qa_chain(query)
        return result["answer"]
