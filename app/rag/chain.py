from typing import Any, List

from openai import AsyncOpenAI
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from app.core.config import get_settings
from app.core.logging import get_logger
from app.rag.citations import build_citations
from app.rag.prompts import build_rag_prompt

logger = get_logger(__name__)
settings = get_settings()


class RAGChain:
    """
    RAG generation layer.

    Supports:
        - OpenAI generation when LLM_PROVIDER=openai
        - Local FLAN-T5 generation when LLM_PROVIDER=local

    This keeps the generation provider replaceable without changing
    retrieval, authorization, or API layers.
    """

    def __init__(self) -> None:
        self.provider = settings.LLM_PROVIDER.lower()
        self.model_name = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS

        self.client = None
        self.tokenizer = None
        self.model = None

        if self.provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError(
                    "OPENAI_API_KEY is required when LLM_PROVIDER=openai"
                )

            self.client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY
            )

        elif self.provider == "local":
            self.model_name = "google/flan-t5-small"

            logger.info(
                "Loading local LLM: %s",
                self.model_name,
            )

            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name
            )

            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_name
            )

            logger.info(
                "Local LLM loaded successfully: %s",
                self.model_name,
            )

        else:
            raise ValueError(
                f"Unsupported LLM provider: {self.provider}"
            )

    async def generate(
        self,
        question: str,
        contexts: List[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Generate a grounded answer from authorized retrieval contexts.
        """

        if not contexts:
            return {
                "answer": (
                    "I do not have enough information in the "
                    "available documents to answer this question."
                ),
                "sources": [],
                "context_used": 0,
            }

        prompt = build_rag_prompt(
            question,
            contexts,
        )

        if self.provider == "openai":
            answer = await self._generate_openai(prompt)

        else:
            answer = self._generate_local(
                question,
                contexts,
            )

        citations = build_citations(contexts)

        logger.info(
            "RAG generation completed | provider=%s | contexts=%d",
            self.provider,
            len(contexts),
        )

        return {
            "answer": answer.strip(),
            "sources": citations,
            "context_used": len(contexts),
        }

    async def _generate_openai(
        self,
        prompt: str,
    ) -> str:
        """Generate using OpenAI."""

        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an enterprise knowledge assistant. "
                        "Answer only using the supplied context. "
                        "Do not invent facts."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        return response.choices[0].message.content or ""

    def _generate_local(
        self,
        question: str,
        contexts: List[dict[str, Any]],
    ) -> str:
        """
        Generate using a local FLAN-T5 model.

        The model receives only retrieved/authorized context.
        """

        context_text = "\n\n".join(
            f"Source: {ctx.get('document_title', 'Unknown')}\n"
            f"{ctx.get('content', '')}"
            for ctx in contexts
        )

        prompt = f"""
Answer the question using ONLY the information in the context below.

If the answer is not present in the context, say:
"I do not have enough information in the available documents."

Be concise and factual.

Context:
{context_text}

Question:
{question}

Answer:
""".strip()

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=min(self.max_tokens, 256),
            do_sample=False,
        )

        answer = self.tokenizer.decode(
            outputs[0],
            skip_special_tokens=True,
        )

        return answer or (
            "I do not have enough information in the "
            "available documents."
        )