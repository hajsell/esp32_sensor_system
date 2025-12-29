let tempChart = null;

export function createTempChart(canvasEl, history) {
  const ctx = canvasEl.getContext("2d");
  if (tempChart) tempChart.destroy();

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

export function updateTempChart(history) {
  if (!tempChart) return;
  tempChart.data.datasets[0].data = history.map(e => ({ x: e.timestamp, y: e.temperature }));
  tempChart.update();
}
