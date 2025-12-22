(function() {
    // 1. CONFIGURATION
    const BACKEND_URL = "https://your-app-name.onrender.com"; // REPLACE THIS WITH RENDER URL
    const BRAND_ID = "cristello"; // Hardcode for this specific store

    // 2. INJECT CSS
    const style = document.createElement('style');
    style.innerHTML = `
        /* --- COPY YOUR ENTIRE CSS CONTENT HERE --- */
        /* Minified CSS is better, but raw works too */
        .chat-widget { position: fixed; bottom: 20px; right: 20px; z-index: 9999; ... }
        /* Add the rest of your CSS styles... */
    `;
    document.head.appendChild(style);

    // 3. CREATE HTML STRUCTURE
    const widgetContainer = document.createElement('div');
    widgetContainer.innerHTML = `
        <button id="chat-toggle-btn" style="position:fixed; bottom:20px; right:20px; z-index:9998; width:60px; height:60px; border-radius:50%; background:#000; color:#fff; border:none; cursor:pointer; box-shadow:0 4px 12px rgba(0,0,0,0.15);">
            💬
        </button>

        <div id="chat-widget" class="chat-widget hidden">
            <div class="chat-header">
                <div class="header-info">
                    <span class="brand-name">Cristello AI</span>
                    <span class="status-text"><div class="status-dot"></div> Online</span>
                </div>
                <button class="close-btn" id="chat-close-btn">×</button>
            </div>
            <div id="chat-messages" class="chat-messages"></div>
            <div class="chat-input-area">
                <input type="text" id="user-input" placeholder="Ask about products...">
                <button id="send-btn">➤</button>
            </div>
        </div>
    `;
    document.body.appendChild(widgetContainer);

    // 4. LOAD LOGIC (Paste your existing JS logic here, slightly modified)
    let sessionId = null;

    // Toggle Logic
    const chatWidget = document.getElementById('chat-widget');
    const toggleBtn = document.getElementById('chat-toggle-btn');
    const closeBtn = document.getElementById('chat-close-btn');

    toggleBtn.onclick = () => {
        chatWidget.classList.remove('hidden');
        toggleBtn.style.display = 'none';
        if (!sessionId) startSession(); // Start session on first open
    };

    closeBtn.onclick = () => {
        chatWidget.classList.add('hidden');
        toggleBtn.style.display = 'block';
    };

    // Chat Logic (Copy your functions: startSession, sendMessage, addMessage here)
    // IMPORTANT: Update all fetch() calls to use BACKEND_URL variable
    async function startSession() {
        try {
            const response = await fetch(`${BACKEND_URL}/start_session`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ brand_id: BRAND_ID })
            });
            const data = await response.json();
            sessionId = data.session_id;
            addMessage("bot", `Hello! Ask me about Cristello products.`);
        } catch (e) { console.error(e); }
    }

    // ... Copy the rest of your JS functions (sendMessage, addMessage) here ...
    
    // Bind Events
    document.getElementById('send-btn').onclick = sendMessage;
    document.getElementById('user-input').onkeypress = (e) => { if(e.key === 'Enter') sendMessage(); };

})();
