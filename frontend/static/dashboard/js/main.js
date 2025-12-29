import { getHistory } from "./api.js";
import { initAllCharts, refreshHistoryCharts, refreshHumidity } from "./charts/index.js";
import { setCurrentValues, applyMinMaxFromHistory } from "./ui.js";
import { connectSocket } from "./socket.js";

let history = [];

async function bootstrap() {
  history = await getHistory();
  setCurrentValues(history[history.length - 1]);
  applyMinMaxFromHistory(history);
  initAllCharts(history);

  connectSocket({
    onNewData: (data) => {
      setCurrentValues(data);
      refreshHumidity(data.humidity);
    },
    onDataSaved: async () => {
      history = await getHistory();
      applyMinMaxFromHistory(history);
      refreshHistoryCharts(history);
    }
  });
}

document.addEventListener("DOMContentLoaded", bootstrap);
