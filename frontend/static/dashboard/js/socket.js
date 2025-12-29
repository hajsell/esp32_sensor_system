export function connectSocket({ onNewData, onDataSaved }) {
  const socket = io();

  socket.on("connect", () => console.log("Połączono z WebSocketem"));
  socket.on("new_data", (data) => onNewData?.(data));
  socket.on("data_saved", () => onDataSaved?.());

  return socket;
}
