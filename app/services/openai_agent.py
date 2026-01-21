import os
import json
from typing import Any
from openai import OpenAI


class OpenAIAgent:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        vector_store_id: str | None = None,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("Brak OPENAI_API_KEY w środowisku (.env).")

        self.model = model or os.getenv("OPENAI_MODEL") or "gpt-4.1"
        self.client = OpenAI(api_key=self.api_key)

        self.vector_store_id = vector_store_id or os.getenv("OPENAI_VECTOR_STORE_ID")

    def _runtime_block(self, current_db: Any, thresholds: Any) -> str:
        parts: list[str] = []

        if current_db is not None:
            parts.append(
                "CURRENT_DB_JSON (źródło prawdy o danych; nie zgaduj):\n"
                + json.dumps(current_db, ensure_ascii=False)
            )

        if thresholds is not None:
            parts.append(
                "THRESHOLDS_JSON (źródło prawdy o progach/alertach; nie zgaduj):\n"
                + json.dumps(thresholds, ensure_ascii=False)
            )

        return "\n\n".join(parts).strip()

    def ask(
        self,
        message: str,
        history: list[dict] | None = None,
        current_db: Any | None = None,
        thresholds: Any | None = None,
    ) -> str:
        history = history or []

        system = (
            "Jesteś pomocnym asystentem w dashboardzie IoT. "
            "Odpowiadaj krótko po polsku. "
            "BIEŻĄCE liczby i stan systemu bierz wyłącznie z CURRENT_DB_JSON i THRESHOLDS_JSON. "
            "Jeśli brakuje danych, powiedz dokładnie czego brakuje. "
            "Nie zmyślaj wartości sensorów."
        )

        messages: list[dict] = [{"role": "system", "content": system}]

        runtime = self._runtime_block(current_db, thresholds)
        if runtime:
            messages.append({"role": "system", "content": runtime})

        for m in history:
            role = m.get("role")
            content = m.get("content")
            if role in ("user", "assistant") and isinstance(content, str):
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": message})

        tools = None
        include = None

        # Jeśli kiedyś dodasz PDF do vector store, to to zadziała automatycznie:
        if self.vector_store_id:
            tools = [{"type": "file_search", "vector_store_ids": [self.vector_store_id]}]
            include = ["file_search_call.results"]

        resp = self.client.responses.create(
            model=self.model,
            input=messages,
            tools=tools,
            include=include,
        )
        return resp.output_text

    def generate_alert_comment(
            self,
            violations: list[str],
            current_db: Any,
            thresholds: Any
    ) -> str:
        system_prompt = (
            "Wykryto przekroczenie norm w systemie IoT! "
            "Zinterpretuj te naruszenia, oceń ryzyko i podaj krótką poradę. "
            "Bądź zwięzły i konkretny. Mów jak ekspert bezpieczeństwa."
        )

        user_msg = f"Wykryte naruszenia: {', '.join(violations)}. Przeanalizuj to."

        # Wykorzystujemy istniejącą logikę runtime_block
        return self.ask(message=user_msg, current_db=current_db, thresholds=thresholds)