import { createTempChart, updateTempChart } from "./tempChart.js";
import { createGasCharts, updateGasCharts } from "./gasCharts.js";
import { createHumidityChart, updateHumidityChart } from "./humidityChart.js";

export function initAllCharts(history) {
  const last = history[history.length - 1] || {};

  const temp = createTempChart(document.getElementById("tempChart"), history);
  const gas  = createGasCharts(
    document.getElementById("mq2Chart"),
    document.getElementById("mq7Chart"),
    history
  );
  const hum  = createHumidityChart(document.getElementById("humidityChart"), last.humidity ?? 0);

  return { temp, gas, hum };
}

export function refreshHistoryCharts(history) {
  updateTempChart(history);
  updateGasCharts(history);
}

export function refreshHumidity(humidity) {
  updateHumidityChart(humidity);
}
