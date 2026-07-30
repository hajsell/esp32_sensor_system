let humidityChart = null;
let minHum = Infinity;
let maxHum = -Infinity;

export function createHumidityChart(canvasEl, humidity) {
  const ctx = canvasEl.getContext("2d");

  if (humidity !== undefined && humidity !== null) {
    updateMinMax(humidity);
  }

  humidityChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      datasets: [{
        data: [humidity, 100 - humidity],
        backgroundColor: ["rgba(54, 162, 235, 0.7)", "rgba(200, 200, 200, 0.2)"],
        borderColor: ["rgba(54, 162, 235, 1)", "rgba(200, 200, 200, 0.3)"],
        borderWidth: 2
      }]
    },
    options: {
      cutout: "80%",
      plugins: {
        legend: { display: true, labels: { color: "#ffffff" } },
        tooltip: {
          callbacks: {
            label: (context) => `${context.label || "Humidity"}: ${context.parsed.toFixed(1)}%`
          }
        }
      }
    }
  });

  return humidityChart;
}

function updateMinMax(humidity) {
  const val = parseFloat(humidity);
  if (isNaN(val)) return;

  if (val < minHum) {
    minHum = val;
    const minEl = document.getElementById("hum-min");
    if (minEl) minEl.innerText = `${minHum.toFixed(1)}%`;
  }

  if (val > maxHum) {
    maxHum = val;
    const maxEl = document.getElementById("hum-max");
    if (maxEl) maxEl.innerText = `${maxHum.toFixed(1)}%`;
  }
}

export function updateHumidityChart(humidity) {
  if (!humidityChart) return;

  const val = parseFloat(humidity);
  updateMinMax(val);

  const humDisplay = document.getElementById("hum");
  if (humDisplay) humDisplay.innerText = `${val.toFixed(1)} %`;

  humidityChart.data.datasets[0].data = [val, 100 - val];
  humidityChart.update();
}