(function () {
  const BRAND_ID = "cristello";
  const API_URL = "https://rag-shopify-a3ho.onrender.com";
  const BRAND_COLOR = "#6b7050";
  const BRAND_COLOR_LIGHT = "#8a9068";
  const LOGO_URL = "https://moinuddin-khan.myshopify.com/cdn/shop/files/download.png";

  let sessionId = null;
  let isOpen = false;
  let isLoaded = false;

  // ===== Inject Styles =====
  const style = document.createElement("style");
  style.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    #cristello-chat-bubble {
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 62px;
      height: 62px;
      border-radius: 50%;
      background: ${BRAND_COLOR};
      box-shadow: 0 4px 20px rgba(107, 112, 80, 0.4);
      cursor: pointer;
      z-index: 99999;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s ease;
      border: none;
      outline: none;
    }
    #cristello-chat-bubble:hover {
      transform: scale(1.08);
      box-shadow: 0 6px 28px rgba(107, 112, 80, 0.5);
    }
    #cristello-chat-bubble svg {
      width: 28px;
      height: 28px;
      fill: white;
      transition: all 0.3s ease;
    }
    #cristello-chat-bubble.open svg.chat-icon { display: none; }
    #cristello-chat-bubble.open svg.close-icon { display: block; }
    #cristello-chat-bubble:not(.open) svg.chat-icon { display: block; }
    #cristello-chat-bubble:not(.open) svg.close-icon { display: none; }

    #cristello-chat-widget {
      position: fixed;
      bottom: 100px;
      right: 24px;
      width: 400px;
      height: 600px;
      max-height: calc(100vh - 130px);
      background: #f8f9fb;
      border-radius: 20px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      z-index: 99998;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      opacity: 0;
      transform: translateY(20px) scale(0.95);
      pointer-events: none;
      transition: opacity 0.35s ease, transform 0.35s ease;
    }
    #cristello-chat-widget.visible {
      opacity: 1;
      transform: translateY(0) scale(1);
      pointer-events: auto;
    }

    /* Header */
    .cw-header {
      background: linear-gradient(135deg, ${BRAND_COLOR}, ${BRAND_COLOR_LIGHT});
      color: white;
      padding: 16px 18px;
      display: flex;
      align-items: center;
      gap: 12px;
      flex-shrink: 0;
    }
    .cw-header-logo {
      height: 22px;
      filter: brightness(0) invert(1);
    }
    .cw-header-info {
      flex: 1;
      display: flex;
      flex-direction: column;
    }
    .cw-header-title {
      font-weight: 700;
      font-size: 15px;
      line-height: 1.2;
    }
    .cw-header-status {
      font-size: 11px;
      color: rgba(255,255,255,0.85);
      display: flex;
      align-items: center;
      gap: 5px;
      margin-top: 2px;
    }
    .cw-status-dot {
      width: 6px;
      height: 6px;
      background: #4ade80;
      border-radius: 50%;
      box-shadow: 0 0 6px rgba(74, 222, 128, 0.6);
    }
    .cw-close {
      background: rgba(255,255,255,0.15);
      border: none;
      color: white;
      width: 32px;
      height: 32px;
      border-radius: 8px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.2s;
    }
    .cw-close:hover { background: rgba(255,255,255,0.25); }
    .cw-close svg { width: 16px; height: 16px; }

    /* Messages */
    .cw-messages {
      flex: 1;
      padding: 16px 14px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 6px;
      scroll-behavior: smooth;
    }
    .cw-messages::-webkit-scrollbar { width: 4px; }
    .cw-messages::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 10px; }

    .cw-msg-row {
      display: flex;
      align-items: flex-end;
      gap: 8px;
      animation: cwMsgIn 0.3s ease;
    }
    .cw-msg-row.user { justify-content: flex-end; }
    .cw-msg-row.bot { justify-content: flex-start; }

    @keyframes cwMsgIn {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .cw-avatar {
      width: 28px;
      height: 28px;
      border-radius: 8px;
      background: linear-gradient(135deg, ${BRAND_COLOR}, ${BRAND_COLOR_LIGHT});
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 12px;
      color: white;
      flex-shrink: 0;
    }

    .cw-bubble {
      padding: 11px 15px;
      border-radius: 16px;
      font-size: 14px;
      line-height: 1.5;
      max-width: 80%;
      word-wrap: break-word;
    }
    .cw-bubble.user {
      background: linear-gradient(135deg, ${BRAND_COLOR}, ${BRAND_COLOR_LIGHT});
      color: white;
      border-bottom-right-radius: 4px;
      box-shadow: 0 2px 8px rgba(107, 112, 80, 0.2);
    }
    .cw-bubble.bot {
      background: white;
      color: #1a1a2e;
      border-bottom-left-radius: 4px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }

    .cw-bubble strong, .cw-bubble b { font-weight: 600; }

    .cw-product-link {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      margin: 5px 3px 3px 0;
      padding: 7px 12px;
      background: linear-gradient(135deg, ${BRAND_COLOR}, ${BRAND_COLOR_LIGHT});
      color: white;
      text-decoration: none;
      font-weight: 600;
      font-size: 12px;
      border-radius: 8px;
      transition: all 0.2s ease;
      box-shadow: 0 2px 6px rgba(107, 112, 80, 0.2);
    }
    .cw-product-link:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(107, 112, 80, 0.3);
    }
    .cw-product-link::after { content: " \\2192"; }

    /* Typing */
    .cw-typing { display: flex; gap: 4px; padding: 4px 2px; }
    .cw-dot {
      width: 7px; height: 7px;
      background: #b0b5c1;
      border-radius: 50%;
      animation: cwBounce 1.4s infinite ease-in-out both;
    }
    .cw-dot:nth-child(1) { animation-delay: -0.32s; }
    .cw-dot:nth-child(2) { animation-delay: -0.16s; }
    @keyframes cwBounce {
      0%, 80%, 100% { transform: scale(0); }
      40% { transform: scale(1); }
    }

    /* Input */
    .cw-input-area {
      padding: 12px 14px;
      background: white;
      border-top: 1px solid #eef0f4;
      display: flex;
      gap: 8px;
      align-items: center;
      flex-shrink: 0;
    }
    .cw-input-area input {
      flex: 1;
      padding: 11px 16px;
      background: #f3f4f8;
      border: 2px solid transparent;
      border-radius: 12px;
      font-size: 14px;
      font-family: inherit;
      outline: none;
      transition: all 0.2s;
      color: #1a1a2e;
    }
    .cw-input-area input::placeholder { color: #9ca3af; }
    .cw-input-area input:focus {
      background: white;
      border-color: ${BRAND_COLOR};
      box-shadow: 0 0 0 3px rgba(107, 112, 80, 0.1);
    }
    .cw-send-btn {
      width: 40px;
      height: 40px;
      background: linear-gradient(135deg, ${BRAND_COLOR}, ${BRAND_COLOR_LIGHT});
      color: white;
      border: none;
      border-radius: 12px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
      flex-shrink: 0;
    }
    .cw-send-btn:hover {
      transform: scale(1.05);
      box-shadow: 0 4px 12px rgba(107, 112, 80, 0.3);
    }
    .cw-send-btn:active { transform: scale(0.95); }
    .cw-send-btn svg { width: 18px; height: 18px; }

    /* Welcome message */
    .cw-welcome {
      text-align: center;
      padding: 24px 16px 8px;
    }
    .cw-welcome-logo {
      height: 28px;
      margin-bottom: 12px;
    }
    .cw-welcome p {
      font-size: 13px;
      color: #6b7280;
      line-height: 1.5;
    }

    /* Responsive */
    @media (max-width: 480px) {
      #cristello-chat-widget {
        width: calc(100vw - 16px);
        height: calc(100vh - 80px);
        max-height: calc(100vh - 80px);
        bottom: 76px;
        right: 8px;
        border-radius: 16px;
      }
      #cristello-chat-bubble {
        bottom: 12px;
        right: 12px;
      }
    }
  `;
  document.head.appendChild(style);

  // ===== Create Bubble =====
  const bubble = document.createElement("button");
  bubble.id = "cristello-chat-bubble";
  bubble.innerHTML = `
    <svg class="chat-icon" viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
    <svg class="close-icon" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
  `;
  bubble.setAttribute("aria-label", "Open chat");
  document.body.appendChild(bubble);

  // ===== Create Widget =====
  const widget = document.createElement("div");
  widget.id = "cristello-chat-widget";
  widget.innerHTML = `
    <div class="cw-header">
      <img class="cw-header-logo" src="${LOGO_URL}" alt="Cristello">
      <div class="cw-header-info">
        <span class="cw-header-title">Shopping Assistant</span>
        <span class="cw-header-status"><span class="cw-status-dot"></span> Online</span>
      </div>
      <button class="cw-close" aria-label="Close chat">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
      </button>
    </div>
    <div class="cw-messages" id="cw-messages">
      <div class="cw-welcome">
        <img class="cw-welcome-logo" src="${LOGO_URL}" alt="Cristello">
        <p>Hi there! I'm your Cristello shopping assistant. Ask me about products, ingredients, or availability.</p>
      </div>
    </div>
    <div class="cw-input-area">
      <input type="text" id="cw-input" placeholder="Ask about our products..." />
      <button class="cw-send-btn" id="cw-send" aria-label="Send">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
      </button>
    </div>
  `;
  document.body.appendChild(widget);

  // ===== Event Handlers =====
  bubble.addEventListener("click", toggleChat);
  widget.querySelector(".cw-close").addEventListener("click", toggleChat);
  document.getElementById("cw-send").addEventListener("click", sendMessage);
  document.getElementById("cw-input").addEventListener("keypress", function (e) {
    if (e.key === "Enter") sendMessage();
  });

  function toggleChat() {
    isOpen = !isOpen;
    widget.classList.toggle("visible", isOpen);
    bubble.classList.toggle("open", isOpen);

    if (isOpen && !isLoaded) {
      isLoaded = true;
      initSession();
    }
  }

  async function initSession() {
    try {
      const res = await fetch(`${API_URL}/start_session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ brand_id: BRAND_ID }),
      });
      const data = await res.json();
      sessionId = data.session_id;
    } catch (err) {
      console.error("Cristello Chat: Failed to start session", err);
    }
  }

  async function sendMessage() {
    const input = document.getElementById("cw-input");
    const message = input.value.trim();
    if (!message || !sessionId) return;

    addMessage("user", message);
    input.value = "";
    input.focus();

    const typingId = addTyping();

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: message }),
      });
      const data = await res.json();
      removeEl(typingId);
      addMessage("bot", data.response);
    } catch (err) {
      removeEl(typingId);
      addMessage("bot", "Sorry, I encountered an error. Please try again.");
      console.error(err);
    }
  }

  function addMessage(role, text) {
    // Remove welcome message on first interaction
    const welcome = document.querySelector(".cw-welcome");
    if (welcome) welcome.remove();

    const container = document.getElementById("cw-messages");
    const row = document.createElement("div");
    row.className = `cw-msg-row ${role}`;

    if (role === "bot") {
      const avatar = document.createElement("div");
      avatar.className = "cw-avatar";
      avatar.textContent = "C";
      row.appendChild(avatar);
    }

    const bubble = document.createElement("div");
    bubble.className = `cw-bubble ${role}`;

    let formatted = text;

    // Links
    formatted = formatted.replace(/\[([^\]]+)\]\(([^)]+)\)/g, function (m, t, u) {
      var label = t.trim().startsWith("http") ? "View Product" : t;
      return '<a href="' + u + '" target="_blank" class="cw-product-link">' + label + "</a>";
    });

    // Bold
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

    // Numbered lists
    formatted = formatted.replace(/(\d+\.)\s/g, "<br><b>$1</b> ");

    // Bullets
    formatted = formatted.replace(/^\*\s/gm, "<br>• ");

    // Newlines
    formatted = formatted.replace(/\n/g, "<br>");

    if (formatted.startsWith("<br>")) formatted = formatted.substring(4);

    bubble.innerHTML = formatted;
    row.appendChild(bubble);

    const id = "msg-" + Date.now();
    row.setAttribute("data-id", id);
    container.appendChild(row);
    container.scrollTop = container.scrollHeight;
    return id;
  }

  function addTyping() {
    const container = document.getElementById("cw-messages");
    const row = document.createElement("div");
    row.className = "cw-msg-row bot";

    const avatar = document.createElement("div");
    avatar.className = "cw-avatar";
    avatar.textContent = "C";
    row.appendChild(avatar);

    const bubble = document.createElement("div");
    bubble.className = "cw-bubble bot";
    bubble.innerHTML = '<div class="cw-typing"><div class="cw-dot"></div><div class="cw-dot"></div><div class="cw-dot"></div></div>';
    row.appendChild(bubble);

    const id = "typing-" + Date.now();
    row.setAttribute("data-id", id);
    container.appendChild(row);
    container.scrollTop = container.scrollHeight;
    return id;
  }

  function removeEl(id) {
    const el = document.querySelector('[data-id="' + id + '"]');
    if (el) el.remove();
  }
})();
