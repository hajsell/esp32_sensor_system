import os
from openai import OpenAI

class OpenAIAgent:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        context_file: str | None = None,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("Brak OPENAI_API_KEY w środowisku.")

        self.model = model
        self.client = OpenAI(api_key=self.api_key)

        self.context_text = ""
        if context_file:
            self.context_text = self._load_context_file(context_file)

    def _load_context_file(self, path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            return ""

    def _build_db_context(self, db_snapshot: dict | None) -> str:
        """
        db_snapshot: mały wycinek danych, NIE cała baza.
        Np. ostatni pomiar + min/max + progi, itp.
        """
        if not db_snapshot:
            return ""

        # Formatuj kontekst tak, żeby model nie zgadywał
        return (
            "DANE Z SYSTEMU (traktuj jako prawdę, nie zgaduj):\n"
            f"{db_snapshot}\n"
        ).strip()

    def ask(
        self,
        message: str,
        history: list[dict] | None = None,
        db_snapshot: dict | None = None,
    ) -> str:
        history = history or []

        system = (
            "Jesteś pomocnym asystentem w dashboardzie IoT. "
            "Odpowiadaj krótko po polsku. "
            "Jeśli brakuje danych, powiedz czego brakuje. "
            "Nie zmyślaj wartości sensorów."
        )

        messages = [{"role": "system", "content": system}]

        # 1) Stały kontekst z pliku (opcjonalnie)
        if self.context_text:
            messages.append({
                "role": "system",
                "content": "KONTEKST PROJEKTU (dokumentacja):\n" + self.context_text
            })

        # 2) Kontekst z bazy (mały snapshot)
        db_ctx = self._build_db_context(db_snapshot)
        if db_ctx:
            messages.append({
                "role": "system",
                "content": db_ctx
            })

        # 3) Historia rozmowy
        for m in history:
            role = m.get("role")
            content = m.get("content")
            if role in ("user", "assistant") and isinstance(content, str):
                messages.append({"role": role, "content": content})

        # 4) Aktualne pytanie
        messages.append({"role": "user", "content": message})

        resp = self.client.responses.create(
            model=self.model,
            input=messages
        )
        return resp.output_text
