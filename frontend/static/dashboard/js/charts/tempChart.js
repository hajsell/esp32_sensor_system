let tempChart = null;
let minTemp = Infinity;
let maxTemp = -Infinity;

export function createTempChart(canvasEl, history) {
  const ctx = canvasEl.getContext("2d");
  if (tempChart) tempChart.destroy();

  if (history && history.length > 0) {
    updateMinMax(history);
  }

  tempChart = new Chart(ctx, {
    type: "line",
    data: {
      datasets: [{
        label: "Temperature (°C)",
        data: history.map(e => ({ x: e.timestamp, y: e.temperature })),
        borderColor: "rgba(255, 99, 132, 1)",
        backgroundColor: "rgba(255, 99, 132, 0.2)",
        fill: true,
        tension: 0.3,
        pointRadius: 2,
      }]
    },
    options: {
      responsive: true,
      scales: {
        x: {
          type: "time",
          time: {
            parser: "yyyy-MM-dd HH:mm:ss",
            unit: "minute",
            displayFormats: { minute: "HH:mm" },
            tooltipFormat: "HH:mm"
          },
          ticks: { color: "#898d99", maxTicksLimit: 8, autoSkip: true, maxRotation: 0 },
          grid: { display: false },
          title: { display: true, text: "Time", color: "#898d99" }
        },
        y: {
          title: { display: true, text: "Temperature (°C)", color: "#898d99" },
          ticks: { color: "#898d99" },
          grid: { color: "#898d99" }
        }
      },
      plugins: {
        legend: { labels: { color: "#898d99" } },
        tooltip: { bodyColor: "#ffffff", backgroundColor: "#1c202c" }
      }
    }
  });

  return tempChart;
}

function updateMinMax(history) {
  if (!history || history.length === 0) return;

  const temperatures = history.map(e => parseFloat(e.temperature)).filter(val => !isNaN(val));
  if (temperatures.length === 0) return;

  const currentMin = Math.min(...temperatures);
  const currentMax = Math.max(...temperatures);

  if (currentMin < minTemp) {
    minTemp = currentMin;
    const minEl = document.getElementById("temp-min");
    if (minEl) minEl.innerText = `${minTemp.toFixed(1)}°C`;
  }

  if (currentMax > maxTemp) {
    maxTemp = currentMax;
    const maxEl = document.getElementById("temp-max");
    if (maxEl) maxEl.innerText = `${maxTemp.toFixed(1)}°C`;
  }

  const latestTemp = temperatures[temperatures.length - 1];
  const tempDisplay = document.getElementById("temp");
  if (tempDisplay) tempDisplay.innerText = `${latestTemp.toFixed(1)}°C`;
}

export function updateTempChart(history) {
  if (!tempChart) return;

  updateMinMax(history);

  tempChart.data.datasets[0].data = history.map(e => ({ x: e.timestamp, y: e.temperature }));
  tempChart.update();
}