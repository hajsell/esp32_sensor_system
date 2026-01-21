export function initThresholds() {
  const form = document.getElementById("thresholds-form");
  if (!form) return;

  const status = document.getElementById("thresholds-status");
  const clearBtn = document.getElementById("thresholds-clear");

  /**
   * 1. POBIERANIE AKTUALNYCH WARTOŚCI Z SERWERA (JSON)
   */
  async function loadThresholds() {
    console.log("Próba pobrania danych z /api/thresholds...");

    try {
      const response = await fetch("/api/thresholds");
      if (!response.ok) throw new Error("Błąd pobierania");

      const data = await response.json();
      console.log("Otrzymany JSON:", data);

      // Wyciągamy obiekt z wnętrza "warning" (zgodnie z Twoją strukturą pliku)
      const nestedData = data.warning;

      if (nestedData) {
        // Mapujemy klucze z JSON (lewa) na atrybuty name w HTML (prawa)
        const mapping = {
          temperature: "temp",
          humidity: "humidity",
          mq2: "mq2",
          mq7: "mq7"
        };

        Object.keys(mapping).forEach(jsonKey => {
          const htmlName = mapping[jsonKey];
          const input = form.elements[htmlName];
          const value = nestedData[jsonKey];

          if (input && value !== undefined) {
            input.value = value;
          }
        });

        setStatus("Wartości zaktualizowane z pliku.");
      } else {
        console.error("Nie znaleziono klucza 'warning' w JSONie");
      }

    } catch (err) {
      console.error("Błąd ładowania:", err);
      setStatus("Nie udało się wczytać progów.");
    }
  }

  // Wywołaj od razu przy starcie strony
  loadThresholds();

  /**
   * FUNKCJE POMOCNICZE
   */
  function setStatus(msg) {
    if (status) {
      status.textContent = msg;
      // Usuń komunikat po 3 sekundach
      setTimeout(() => { status.textContent = ""; }, 3000);
    }
  }

  function readNumber(name) {
    const el = form.elements[name];
    const val = parseFloat(el?.value);
    // Jeśli pole jest puste lub błędne, zwracamy 0 lub inną wartość domyślną
    return isNaN(val) ? 0 : val;
  }

  /**
   * 2. ZAPISYWANIE DANYCH (POST)
   */
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    // Budujemy strukturę identyczną jak w pliku JSON (zagnieżdżone w warning)
    const payload = {
      warning: {
        temperature: readNumber("temp"),
        humidity: readNumber("humidity"),
        mq2: readNumber("mq2"),
        mq7: readNumber("mq7")
      }
    };

    try {
      setStatus("Zapisywanie...");
      const response = await fetch("/api/thresholds", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        setStatus("Progi zapisane pomyślnie! ✓");
      } else {
        throw new Error("Błąd serwera");
      }
    } catch (err) {
      console.error("Błąd zapisu:", err);
      setStatus("Błąd podczas zapisu.");
    }
  });

  /**
   * 3. PRZYCISK PRZYWRACANIA (Wcześniej: Wyczyść)
   */
  clearBtn?.addEventListener("click", () => {
    // Zamiast form.reset(), wywołujemy ponownie ładowanie danych z serwera
    loadThresholds();
    setStatus("Przywrócono ostatnio zapisane wartości.");
  });
}