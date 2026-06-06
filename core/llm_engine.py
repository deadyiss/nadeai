import time
from typing import Optional

import config
from utils.logger import get_logger

logger = get_logger(__name__)


class LLMEngine:
    def __init__(self):
        self.model = config.LLM_MODEL
        self.provider = config.LLM_PROVIDER

        if self.provider == "groq":
            import groq as groq_sdk
            self.client = groq_sdk.Groq(api_key=config.GROQ_API_KEY)
        elif self.provider == "ollama":
            import ollama as ollama_sdk
            self.client = ollama_sdk.Client(host=config.OLLAMA_HOST)
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

        logger.info(f"LLM engine init: provider={self.provider} model={self.model}")

    def health_check(self) -> bool:
        try:
            if self.provider == "groq":
                self.client.models.list()
            elif self.provider == "ollama":
                import ollama as ollama_sdk
                ollama_sdk.Client(host=config.OLLAMA_HOST).list()
            return True
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return False

    def build_prompt(self, query: str, context_chunks: list[dict]) -> str:
        if not context_chunks:
            context_str = "(no relevant documents found)"
        else:
            blocks = []
            for i, c in enumerate(context_chunks, 1):
                sim = c.get('similarity', 0)
                text = c.get('text', '').strip()
                blocks.append(
                    f"[Document {i}: {c.get('filename', 'unknown')} "
                    f"| relevance={sim:.2f}]\n"
                    f"{text}"
                )
            context_str = "\n\n".join(blocks)

        system = (
            "You are a thorough, analytical document assistant. "
            "Your job is to answer questions based SOLELY on the provided documents — "
            "never use outside knowledge.\n\n"

            "HOW TO ANSWER:\n"
            "1. Give a complete, well-structured answer. Do not truncate or oversimplify.\n"
            "2. Always cite your source inline using [Document N] or the filename after every claim.\n"
            "3. If multiple documents mention the same topic with DIFFERENT values or dates, "
            "you MUST present ALL versions and their sources. "
            "Example: 'According to [Document 1] the figure is X, however [Document 3] states Y, "
            "and [Document 5] reports Z.'\n"
            "4. After presenting conflicting data, briefly note which source is likely most "
            "authoritative (e.g. official minutes > internal reports > early estimates) "
            "and why — but do not make up reasoning beyond what the documents imply.\n"
            "5. Answer in the SAME LANGUAGE as the question.\n"
            "6. Use natural, clear prose. You may use short paragraphs or a brief list "
            "when presenting multiple conflicting values — whatever is clearest.\n"
            "7. Related terms are valid matches "
            "(e.g. 'anggaran' = 'budget', 'pegawai' = 'karyawan').\n"
            "8. If the documents genuinely do not contain the answer, say exactly: "
            "\"Dokumen yang tersedia tidak memuat informasi yang cukup untuk menjawab pertanyaan ini.\"\n"
            "9. Never invent, extrapolate, or add context not present in the documents.\n"
            "10. Do not add a preamble like 'Great question!' or a closing like 'I hope this helps.'"
        )

        user = (
            f"=== DOCUMENTS ===\n{context_str}\n\n"
            f"=== QUESTION ===\n{query.strip()}"
        )

        return system, user

    def generate(
        self,
        prompt,
        temperature: float = 0.2,
        max_tokens: int = 300,
        timeout_seconds: Optional[float] = None,
    ) -> dict:
        system_msg, user_msg = prompt
        start = time.time()

        try:
            if self.provider == "groq":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                elapsed = (time.time() - start) * 1000
                text = response.choices[0].message.content.strip()
                tokens = response.usage.completion_tokens if response.usage else None

            elif self.provider == "ollama":
                response = self.client.chat(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg},
                    ],
                    options={"temperature": temperature, "num_predict": max_tokens},
                )
                elapsed = (time.time() - start) * 1000
                text = response["message"]["content"].strip()
                tokens = response.get("eval_count")

            return {
                "text": text,
                "model": self.model,
                "elapsed_ms": round(elapsed, 2),
                "tokens_predicted": tokens,
            }

        except Exception as e:
            elapsed = (time.time() - start) * 1000
            logger.error(f"LLM generate failed after {elapsed:.0f}ms: {e}")
            raise

    def answer(
        self,
        query: str,
        context_chunks: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 800,
    ) -> dict:
        prompt = self.build_prompt(query, context_chunks)
        result = self.generate(prompt, temperature=temperature, max_tokens=max_tokens)
        system_msg, user_msg = prompt
        result["prompt_chars"] = len(system_msg) + len(user_msg)
        return result


_engine: Optional[LLMEngine] = None


def get_llm_engine() -> LLMEngine:
    global _engine
    if _engine is None:
        _engine = LLMEngine()
    return _engine