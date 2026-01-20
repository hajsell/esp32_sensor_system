export function initThresholds() {
  const form = document.getElementById("thresholds-form");
  if (!form) return;

  const status = document.getElementById("thresholds-status");
  const clearBtn = document.getElementById("thresholds-clear");

  // Tylko w pamięci (RAM) — po refresh zniknie
  const thresholds = {
    temp: null,
    humidity: null,
    mq2: null,
    mq7: null,
  };

  function setStatus(msg) {
    if (status) status.textContent = msg;
  }

  function readNumber(name) {
    const el = form.elements[name];
    const raw = (el?.value ?? "").toString().trim();
    if (!raw) return null;
    const val = Number(raw);
    return Number.isFinite(val) ? val : null;
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();

    thresholds.temp = readNumber("temp");
    thresholds.humidity = readNumber("humidity");
    thresholds.mq2 = readNumber("mq2");
    thresholds.mq7 = readNumber("mq7");

    setStatus("Ustawiono lokalnie ✓ (nie zapisuję nigdzie)");
    // Jakbyś chciał podejrzeć w konsoli:
    // console.log("thresholds:", thresholds);
  });

  clearBtn?.addEventListener("click", () => {
    form.reset();
    thresholds.temp = thresholds.humidity = thresholds.mq2 = thresholds.mq7 = null;
    setStatus("Wyczyszczono.");
  });
}
