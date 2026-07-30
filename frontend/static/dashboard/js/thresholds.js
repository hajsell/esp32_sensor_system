export function initThresholds() {
  const form = document.getElementById("thresholds-form");
  if (!form) return;

  const status = document.getElementById("thresholds-status");
  const clearBtn = document.getElementById("thresholds-clear");

  async function loadThresholds() {
    console.log("Próba pobrania danych z /api/thresholds...");

    try {
      const response = await fetch("/api/thresholds");
      if (!response.ok) throw new Error("Błąd pobierania");

      const data = await response.json();
      console.log("Otrzymany JSON:", data);

      const nestedData = data.warning;

      if (nestedData) {
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

  loadThresholds();

  function setStatus(msg) {
    if (status) {
      status.textContent = msg;
      setTimeout(() => { status.textContent = ""; }, 3000);
    }
  }

  function readNumber(name) {
    const el = form.elements[name];
    const val = parseFloat(el?.value);
    return isNaN(val) ? 0 : val;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

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

  clearBtn?.addEventListener("click", () => {
    loadThresholds();
    setStatus("Przywrócono ostatnio zapisane wartości.");
  });
}