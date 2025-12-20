let sessionId = null;
const API_URL = "http://localhost:8000";

async function startSession(brandId) {
    try {
        const response = await fetch(`${API_URL}/start_session`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ brand_id: brandId })
        });
        const data = await response.json();
        sessionId = data.session_id;
        
        // UI Transitions
        document.querySelector('.brand-selector').classList.add('hidden');
        const chatWidget = document.querySelector('#chat-widget');
        chatWidget.classList.remove('hidden');
        
        // Update Header
        document.getElementById('brand-title').innerText = brandId.charAt(0).toUpperCase() + brandId.slice(1);
        
        // Initial Greeting
        setTimeout(() => {
            addMessage("bot", `Hello! I am your ${brandId} AI assistant. Ask me about products, ingredients, or availability.`);
        }, 500); // Small delay for effect

    } catch (error) {
        alert("Failed to connect to backend. Is it running?");
        console.error(error);
    }
}

async function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();
    if (!message) return;

    // 1. Add User Message immediately
    addMessage("user", message);
    input.value = "";
    input.focus();

    // 2. Add Typing Indicator
    const typingId = addTypingIndicator();

    try {
        // 3. API Call
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, message: message })
        });
        const data = await response.json();
        
        // 4. Remove Typing Indicator
        removeMessage(typingId);

        // 5. Add Bot Response
        addMessage("bot", data.response);

    } catch (error) {
        removeMessage(typingId);
        addMessage("bot", "Sorry, I encountered an error connecting to the server.");
        console.error(error);
    }
}

function addMessage(role, text) {
    const messagesDiv = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    
    // --- Markdown Parsing ---
    let formattedText = text;

    // Links: [Text](URL) -> Pill Button
    formattedText = formattedText.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, linkText, url) => {
        const displayLabel = linkText.trim().startsWith('http') ? 'View Product' : linkText;
        return `<a href="${url}" target="_blank" class="product-link">${displayLabel}</a>`;
    });

    // Bold: **Text**
    formattedText = formattedText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Lists: 1. Item -> New line + Bold Item
    formattedText = formattedText.replace(/(\d+\.)\s/g, '<br><b>$1</b> ');
    
    // Bullets: * Item -> New line + Bullet
    formattedText = formattedText.replace(/^\*\s/gm, '<br>• ');

    // Newlines
    formattedText = formattedText.replace(/\n/g, '<br>');
    
    // Clean start
    if (formattedText.startsWith('<br>')) formattedText = formattedText.substring(4);

    div.innerHTML = formattedText;
    
    const id = Date.now();
    div.setAttribute("data-id", id);
    messagesDiv.appendChild(div);
    scrollToBottom();
    return id;
}

function addTypingIndicator() {
    const messagesDiv = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `message bot typing`;
    div.innerHTML = `
        <div class="typing-dots">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        </div>
    `;
    const id = "typing-" + Date.now();
    div.setAttribute("data-id", id);
    messagesDiv.appendChild(div);
    scrollToBottom();
    return id;
}

function removeMessage(id) {
    const msg = document.querySelector(`.message[data-id="${id}"]`);
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