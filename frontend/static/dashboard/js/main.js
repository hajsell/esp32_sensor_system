import { getHistory } from "./api.js";
import { initAllCharts, refreshHistoryCharts, refreshHumidity } from "./charts/index.js";
import { setCurrentValues, applyMinMaxFromHistory } from "./ui.js";
import { connectSocket } from "./socket.js";
import { initAIChat } from "./ai_chat.js";
import { initThresholds } from "./thresholds.js"

let history = [];

async function bootstrap() {
  history = await getHistory();
  setCurrentValues(history[history.length - 1]);
  applyMinMaxFromHistory(history);
  initAllCharts(history);
  initThresholds();
  initAIChat();

  connectSocket({
    onNewData: (data) => {
      setCurrentValues(data);
      refreshHumidity(data.humidity);
    },
    onDataSaved: async () => {
      history = await getHistory();
      applyMinMaxFromHistory(history);
      refreshHistoryCharts(history);
    },
    // DODAJ TO:
    onAIAlert: (alertData) => {
      window.addAIAlertToChat?.(alertData);
    }
  });
}

document.addEventListener("DOMContentLoaded", bootstrap);
