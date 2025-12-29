let humidityChart = null;

export function createHumidityChart(canvasEl, humidity) {
  const ctx = canvasEl.getContext("2d");

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

export function updateHumidityChart(humidity) {
  if (!humidityChart) return;
  humidityChart.data.datasets[0].data = [humidity, 100 - humidity];
  humidityChart.update();
}
