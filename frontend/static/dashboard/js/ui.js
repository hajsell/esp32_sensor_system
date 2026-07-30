function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

export function setCurrentValues(data) {
  if (!data) return;
  setText("temp", data.temperature != null ? `${data.temperature.toFixed(1)} °C` : "-- °C");
  setText("hum",  data.humidity != null ? `${data.humidity} %` : "-- %");
  setText("mq2Current", data.mq2 != null ? `${data.mq2}` : "--");
  setText("mq7Current", data.mq7 != null ? `${data.mq7}` : "--");
}

export function applyMinMaxFromHistory(history) {
  const temps = history.map(x => x.temperature).filter(n => typeof n === "number");
  const hums  = history.map(x => x.humidity).filter(n => typeof n === "number");

  if (temps.length) {
    setText("temp-max", `${Math.max(...temps).toFixed(1)} °C`);
    setText("temp-min", `${Math.min(...temps).toFixed(1)} °C`);
  }
  if (hums.length) {
    setText("hum-max", `${Math.max(...hums).toFixed(1)} %`);
    setText("hum-min", `${Math.min(...hums).toFixed(1)} %`);
  }
}
