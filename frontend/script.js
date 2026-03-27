let sessionId = null;
let currentBrand = null;

const API_URL = window.location.hostname === "localhost"
    ? "http://localhost:8000"
    : "https://rag-shopify-a3ho.onrender.com";

async function startSession(brandId) {
    try {
        const response = await fetch(`${API_URL}/start_session`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ brand_id: brandId })
        });
        const data = await response.json();
        sessionId = data.session_id;
        currentBrand = brandId;

        document.getElementById('brand-selector').classList.add('hidden');
        const chatWidget = document.getElementById('chat-widget');
        chatWidget.classList.remove('hidden');
        chatWidget.classList.add(`brand-${brandId}`);

        document.getElementById('brand-title').innerText = brandId.charAt(0).toUpperCase() + brandId.slice(1);
        document.getElementById('header-avatar').innerText = brandId.charAt(0).toUpperCase();

        setTimeout(() => {
            addMessage("bot", `Hello! I am your ${brandId.charAt(0).toUpperCase() + brandId.slice(1)} AI assistant. Ask me about products, ingredients, or availability.`);
        }, 400);

    } catch (error) {
        alert("Failed to connect to backend. Is it running?");
        console.error(error);
    }
}

async function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();
    if (!message) return;

    addMessage("user", message);
    input.value = "";
    input.focus();

    const typingId = addTypingIndicator();

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, message: message })
        });
        const data = await response.json();
        removeMessage(typingId);
        addMessage("bot", data.response);

    } catch (error) {
        removeMessage(typingId);
        addMessage("bot", "Sorry, I encountered an error connecting to the server.");
        console.error(error);
    }
}

function addMessage(role, text) {
    const messagesDiv = document.getElementById('chat-messages');

    const row = document.createElement('div');
    row.className = `message-row ${role}`;

    if (role === "bot") {
        const avatar = document.createElement('div');
        avatar.className = `bot-avatar ${currentBrand}-bg`;
        avatar.innerText = currentBrand ? currentBrand.charAt(0).toUpperCase() : 'A';
        row.appendChild(avatar);
    }

    const bubble = document.createElement('div');
    bubble.className = `message ${role}`;

    let formattedText = text;

    // Links: [Text](URL) -> styled button
    formattedText = formattedText.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, linkText, url) => {
        const displayLabel = linkText.trim().startsWith('http') ? 'View Product' : linkText;
        return `<a href="${url}" target="_blank" class="product-link">${displayLabel}</a>`;
    });

    // Bold
    formattedText = formattedText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Numbered lists
    formattedText = formattedText.replace(/(\d+\.)\s/g, '<br><b>$1</b> ');

    // Bullets
    formattedText = formattedText.replace(/^\*\s/gm, '<br>• ');

    // Newlines
    formattedText = formattedText.replace(/\n/g, '<br>');

    // Clean leading break
    if (formattedText.startsWith('<br>')) formattedText = formattedText.substring(4);

    bubble.innerHTML = formattedText;

    const id = Date.now();
    row.setAttribute("data-id", id);
    row.appendChild(bubble);
    messagesDiv.appendChild(row);
    scrollToBottom();
    return id;
}

function addTypingIndicator() {
    const messagesDiv = document.getElementById('chat-messages');

    const row = document.createElement('div');
    row.className = 'message-row bot';

    const avatar = document.createElement('div');
    avatar.className = `bot-avatar ${currentBrand}-bg`;
    avatar.innerText = currentBrand ? currentBrand.charAt(0).toUpperCase() : 'A';
    row.appendChild(avatar);

    const bubble = document.createElement('div');
    bubble.className = 'message bot';
    bubble.innerHTML = `<div class="typing-dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>`;
    row.appendChild(bubble);

    const id = "typing-" + Date.now();
    row.setAttribute("data-id", id);
    messagesDiv.appendChild(row);
    scrollToBottom();
    return id;
}

function removeMessage(id) {
    const msg = document.querySelector(`.message-row[data-id="${id}"]`);
    if (msg) msg.remove();
}

function scrollToBottom() {
    const messagesDiv = document.getElementById('chat-messages');
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function handleKeyPress(e) {
    if (e.key === 'Enter') sendMessage();
}

function closeChat() {
    location.reload();
}
