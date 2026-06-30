import json

from groq import Groq
from openai import OpenAI

from app.config import get_settings
from app.rag.prompting import SYSTEM_PROMPT
from app.utils.exceptions import LLMError


class LLMService:
    def __init__(self):
        self.settings = get_settings()
        self.provider = self.settings.llm_provider.lower()
        self._groq = Groq(api_key=self.settings.groq_api_key) if self.settings.groq_api_key else None
        self._openai = OpenAI(api_key=self.settings.openai_api_key) if self.settings.openai_api_key else None

    def _chat_groq(self, user_prompt: str) -> str:
        if not self._groq:
            raise LLMError("GROQ_API_KEY missing")
        completion = self._groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )
        return completion.choices[0].message.content or ""

    def _chat_openai(self, user_prompt: str) -> str:
        if not self._openai:
            raise LLMError("OPENAI_API_KEY missing")
        completion = self._openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )
        return completion.choices[0].message.content or ""

    def ask(self, user_prompt: str) -> str:
        try:
            if self.provider == "groq":
                return self._chat_groq(user_prompt)
            return self._chat_openai(user_prompt)
        except Exception:
            if self.provider == "groq":
                return self._chat_openai(user_prompt)
            return self._chat_groq(user_prompt)

    def rewrite_query(self, question: str) -> str:
        prompt = (
            "Rewrite the question to make it explicit for document retrieval. "
            "Keep intent unchanged and return only one sentence.\n"
            f"Question: {question}"
        )
        try:
            return self.ask(prompt).strip() or question
        except Exception:
            return question

    @staticmethod
    def parse_answer_and_citations(raw: str) -> tuple[str, list[dict]]:
        try:
            if "```json" in raw:
                json_blob = raw.split("```json", 1)[1].split("```", 1)[0].strip()
                data = json.loads(json_blob)
                return data.get("answer", ""), data.get("citations", [])
        except Exception:
            pass
        return raw.strip(), []
