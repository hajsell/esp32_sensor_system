export function connectSocket({ onNewData, onDataSaved, onAIAlert }) {
  const socket = io();

  socket.on("connect", () => console.log("Połączono z WebSocketem"));
  socket.on("new_data", (data) => onNewData?.(data));
  socket.on("data_saved", () => onDataSaved?.());

  socket.on("ai_alert", (data) => onAIAlert?.(data));

  return socket;
}