// frontend/static/dashboard/js/ai_chat.js

export function initAIChat() {
  const root = document.getElementById("ai-chat");
  if (!root) {
    console.warn("[AI CHAT] #ai-chat not found");
    return;
  }

  const messagesEl = root.querySelector("#ai-chat-messages");
  const form = root.querySelector("#ai-chat-form");
  const input = root.querySelector("#ai-chat-input");
  const sendBtn = root.querySelector("#ai-chat-send");

  const history = [];

  function time() {
    return new Date().toLocaleTimeString("pl-PL", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function addMessage(role, text) {
    const row = document.createElement("div");
    row.className = `ai-chat-row ${role}`;

    const bubble = document.createElement("div");
    bubble.className = "ai-chat-bubble";
    bubble.textContent = text;

    const meta = document.createElement("div");
    meta.className = "ai-chat-meta";
    meta.textContent = `${role === "user" ? "Ty" : "AI"} • ${time()}`;

    const wrap = document.createElement("div");
    wrap.appendChild(bubble);
    wrap.appendChild(meta);

    row.appendChild(wrap);
    messagesEl.appendChild(row);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  async function callBackend(message) {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history }),
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.reply || `HTTP ${res.status}`);
    }
    return data.reply;
  }

  async function handleSend(text) {
    addMessage("user", text);
    history.push({ role: "user", content: text });

    sendBtn.disabled = true;
    input.disabled = true;

    try {
      const reply = await callBackend(text);
      addMessage("bot", reply);
      history.push({ role: "assistant", content: reply });
    } catch (err) {
      addMessage("bot", `Błąd: ${err.message}`);
    } finally {
      sendBtn.disabled = false;
      input.disabled = false;
      input.focus();
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    handleSend(text);
  });

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      form.requestSubmit();
    }
  });

  addMessage("bot", "Czat gotowy. Backend podłączony.");
}
