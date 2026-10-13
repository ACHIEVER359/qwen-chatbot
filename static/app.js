(() => {
  const $ = (id) => document.getElementById(id);
  const form = $("chat-form");
  const input = $("message-input");
  const send = $("send-button");
  const welcome = $("welcome");
  const messagesEl = $("messages");
  const toast = $("toast");

  let history = [];
  let busy = false;

  function showToast(text) {
    toast.textContent = text;
    toast.classList.add("show");
    window.setTimeout(() => toast.classList.remove("show"), 3500);
  }

  function renderMessage(role, content, typing = false) {
    welcome.classList.add("hidden");
    messagesEl.classList.remove("hidden");
    const article = document.createElement("article");
    article.className = `message ${role}`;
    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = role === "assistant" ? "✳" : "Y";
    const contentWrap = document.createElement("div");
    contentWrap.className = "message-content";
    if (role === "assistant") {
      const label = document.createElement("div");
      label.className = "message-label";
      label.textContent = "QWEN ASSISTANT";
      contentWrap.appendChild(label);
    }
    const body = document.createElement("div");
    body.className = "message-text";
    if (typing) {
      body.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';
    } else {
      body.textContent = content;
    }
    contentWrap.appendChild(body);
    article.append(avatar, contentWrap);
    messagesEl.appendChild(article);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return { article, body };
  }

  async function sendMessage(rawText) {
    const message = (rawText || "").trim();
    if (!message || busy) return;
    if (message.length > 4000) {
      showToast("Keep your message under 4,000 characters.");
      return;
    }

    busy = true;
    input.value = "";
    input.style.height = "auto";
    input.disabled = true;
    send.disabled = true;
    renderMessage("user", message);
    const pending = renderMessage("assistant", "", true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, history })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "The assistant couldn't respond.");
      pending.body.textContent = data.reply;
      history.push({ role: "user", content: message });
      history.push({ role: "assistant", content: data.reply });
      history = history.slice(-10);
    } catch (error) {
      pending.body.textContent = error.message || "Something went wrong. Please try again.";
      showToast(error.message || "Something went wrong.");
    } finally {
      busy = false;
      input.disabled = false;
      send.disabled = false;
      input.focus();
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }
  }

  function clearChat() {
    history = [];
    messagesEl.replaceChildren();
    messagesEl.classList.add("hidden");
    welcome.classList.remove("hidden");
    input.value = "";
    input.focus();
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    sendMessage(input.value);
  });

  input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 150)}px`;
  });

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  document.querySelectorAll("[data-prompt]").forEach((button) => {
    button.addEventListener("click", () => sendMessage(button.dataset.prompt));
  });

  $("clear-chat").addEventListener("click", clearChat);
  $("new-chat").addEventListener("click", clearChat);

  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      clearChat();
    }
  });

  fetch("/api/health")
    .then((response) => response.json())
    .then((data) => {
      if (data.status !== "ok") showToast("The server may not be ready.");
    })
    .catch(() => showToast("Could not reach the server. Refresh or check deployment logs."));
})();
