let errorTimeout = null;
function showError(msg) {
  const banner = document.getElementById("error-banner");
  banner.textContent = msg;
  banner.style.display = "block";
  clearTimeout(errorTimeout);
  errorTimeout = setTimeout(() => { banner.style.display = "none"; }, 4000);
}

function initChatPanel(roomId, userName) {
  const messagesEl = document.getElementById("messages");
  const feed = new MessageFeed(messagesEl, userName);
  let currentSocket = null;

  messagesEl.addEventListener("scroll", () => feed.onScroll());

  const sendMessage = () => {
    const input = document.getElementById("message-input");
    const body = input.value.trim();
    if (!body) return;
    if (!currentSocket || currentSocket.readyState !== WebSocket.OPEN) {
      showError("Failed to send message. Connection may be closed.");
      return;
    }
    currentSocket.send(JSON.stringify({
      type: "send_message",
      display_name: userName,
      body,
    }));
    input.value = "";
  };

  document.getElementById("send-button").addEventListener("click", sendMessage);
  document.getElementById("message-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
  });

  function connectSocket(depth) {
    const socket = new WebSocket(
      (window.location.protocol === "https:" ? "wss://" : "ws://") + window.location.host + "/ws/chat/" + roomId + "/"
    );
    currentSocket = socket;

    feed.requestHistory = (offset, count) =>
      socket.send(JSON.stringify({ type: "get_history", offset, count }));

    socket.onerror = () =>
      showError("Connection error. Messages may not be sending.");

    socket.onmessage = (e) => {
      const data = JSON.parse(e.data);
      switch (data.type) {
        case "message": feed.addNewMessage(data); break;
        case "history": feed.onHistory(data); break;
        default: console.error("Unknown message type", data); break;
      }
    };

    socket.onclose = () => {
      if (depth > 5) {
        console.error('Socket disconnected. Max re-connect retries exceeded. To try again reload the page.');
        return;
      }
      const timeoutMs = 2000 * Math.pow(depth, 2);
      setTimeout(() => connectSocket(depth + 1), timeoutMs);
    };
  }

  connectSocket(0);
}
