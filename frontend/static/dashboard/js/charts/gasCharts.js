let mq2Chart = null;
let mq7Chart = null;

export function createGasCharts(mq2Canvas, mq7Canvas, history) {
  const mq2Ctx = mq2Canvas.getContext("2d");
  const mq7Ctx = mq7Canvas.getContext("2d");

  const mq2Data = history.map(e => ({ x: e.timestamp, y: e.mq2 }));
  const mq7Data = history.map(e => ({ x: e.timestamp, y: e.mq7 }));

  mq2Chart = new Chart(mq2Ctx, {
    type: "line",
    data: { datasets: [{ label: "MQ-2", data: mq2Data, borderColor: "#ff9f40", backgroundColor: "rgba(255, 159, 64, 0.2)", fill: true, tension: 0.4, pointRadius: 1 }] },
    options: baseGasOptions()
  });

  mq7Chart = new Chart(mq7Ctx, {
    type: "line",
    data: { datasets: [{ label: "MQ-7", data: mq7Data, borderColor: "#36a2eb", backgroundColor: "rgba(54, 162, 235, 0.2)", fill: true, tension: 0.4, pointRadius: 1 }] },
    options: baseGasOptions()
  });

  return { mq2Chart, mq7Chart };
}

export function updateGasCharts(history) {
  if (!mq2Chart || !mq7Chart) return;

  mq2Chart.data.datasets[0].data = history.map(e => ({ x: e.timestamp, y: e.mq2 }));
  mq7Chart.data.datasets[0].data = history.map(e => ({ x: e.timestamp, y: e.mq7 }));

  mq2Chart.update();
  mq7Chart.update();
}

function baseGasOptions() {
  return {
    responsive: false,
    plugins: { legend: { labels: { color: "#ffffff" } } },
    scales: {
      x: {
        type: "time",
        time: {
          parser: "yyyy-MM-dd HH:mm:ss",
          unit: "minute",
          displayFormats: { minute: "HH:mm" },
          tooltipFormat: "HH:mm"
        },
        ticks: { color: "#ccc", maxTicksLimit: 8, maxRotation: 0, autoSkip: true },
        grid: { display: false }
      },
      y: {
        ticks: { color: "#ccc" },
        grid: { color: "#444" }
      }
    }
  };
}
