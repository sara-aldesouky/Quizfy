#!/usr/bin/env python
"""Script to update the Teacher Help Bot UI in teacher_folders.html"""

NEW_HELPBOT_UI = '''<!-- ✅ Smart Teacher Help Bot Widget -->
<div id="helpbot" class="helpbot">
  <div class="helpbot-header">
    <div class="helpbot-header-left">
      <span class="helpbot-icon">🤖</span>
      <div>
        <div class="helpbot-title">Quizfy Assistant</div>
        <div class="helpbot-subtitle">Ask me anything!</div>
      </div>
    </div>
    <button id="helpbot-toggle" class="helpbot-toggle" type="button">−</button>
  </div>

  <div id="helpbot-body" class="helpbot-body">
    <div class="helpbot-msg bot">
      <div class="bot-avatar">🤖</div>
      <div class="bot-content">
        👋 <strong>Hello!</strong> I'm your Quizfy Assistant.<br><br>
        I can help you with:<br>
        • Creating quizzes & folders<br>
        • Grading submissions<br>
        • Exporting to Excel<br>
        • Using analytics<br><br>
        <em>Try one of the quick questions below or type your own!</em>
      </div>
    </div>
  </div>

  <!-- Quick suggestion buttons -->
  <div id="helpbot-suggestions" class="helpbot-suggestions">
    <button type="button" class="suggestion-btn" data-q="How do I create a quiz?">📝 Create quiz</button>
    <button type="button" class="suggestion-btn" data-q="How do I grade file uploads?">✏️ Grading</button>
    <button type="button" class="suggestion-btn" data-q="How do I export to Excel?">📥 Export</button>
    <button type="button" class="suggestion-btn" data-q="How do I use analytics?">📊 Analytics</button>
  </div>

  <form id="helpbot-form" class="helpbot-form">
    {% csrf_token %}
    <input id="helpbot-input" class="helpbot-input" type="text"
           placeholder="Type your question..." autocomplete="off" />
    <button class="helpbot-send" type="submit">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M22 2L11 13"></path>
        <path d="M22 2L15 22L11 13L2 9L22 2Z"></path>
      </svg>
    </button>
  </form>
</div>

<style>
  .helpbot {
    position: fixed;
    right: 24px;
    bottom: 24px;
    width: 380px;
    max-width: calc(100vw - 48px);
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.1);
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
    color: #e5e7eb;
    z-index: 9999;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .helpbot-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 18px;
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    color: white;
  }
  
  .helpbot-header-left {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .helpbot-icon {
    font-size: 28px;
    animation: bounce 2s infinite;
  }
  
  @keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-3px); }
  }
  
  .helpbot-title {
    font-weight: 700;
    font-size: 15px;
  }
  
  .helpbot-subtitle {
    font-size: 11px;
    opacity: 0.85;
    margin-top: 2px;
  }
  
  .helpbot-toggle {
    border: 0;
    background: rgba(255, 255, 255, 0.2);
    color: white;
    font-size: 20px;
    cursor: pointer;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
  }
  
  .helpbot-toggle:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: scale(1.1);
  }
  
  .helpbot-body {
    padding: 16px;
    height: 300px;
    overflow-y: auto;
    background: linear-gradient(180deg, #0f172a 0%, #0c1322 100%);
    scroll-behavior: smooth;
  }
  
  .helpbot-body::-webkit-scrollbar {
    width: 6px;
  }
  
  .helpbot-body::-webkit-scrollbar-track {
    background: transparent;
  }
  
  .helpbot-body::-webkit-scrollbar-thumb {
    background: rgba(99, 102, 241, 0.3);
    border-radius: 3px;
  }
  
  .helpbot-msg {
    margin-bottom: 14px;
    animation: fadeIn 0.3s ease-out;
  }
  
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
  
  .helpbot-msg.user {
    display: flex;
    justify-content: flex-end;
  }
  
  .helpbot-msg.user .user-content {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    color: white;
    padding: 12px 16px;
    border-radius: 18px 18px 4px 18px;
    max-width: 85%;
    font-size: 13px;
    line-height: 1.5;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
  }
  
  .helpbot-msg.bot {
    display: flex;
    gap: 10px;
    align-items: flex-start;
  }
  
  .bot-avatar {
    width: 32px;
    height: 32px;
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    flex-shrink: 0;
  }
  
  .bot-content {
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(99, 102, 241, 0.2);
    padding: 14px 16px;
    border-radius: 4px 18px 18px 18px;
    max-width: calc(100% - 44px);
    font-size: 13px;
    line-height: 1.6;
  }
  
  .bot-content strong {
    color: #a5b4fc;
  }
  
  .bot-content em {
    color: #94a3b8;
    font-style: normal;
  }
  
  /* Typing indicator */
  .typing-indicator {
    display: flex;
    gap: 4px;
    padding: 8px 0;
  }
  
  .typing-indicator span {
    width: 8px;
    height: 8px;
    background: #6366f1;
    border-radius: 50%;
    animation: typing 1.4s infinite;
  }
  
  .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
  .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
  
  @keyframes typing {
    0%, 100% { transform: translateY(0); opacity: 0.5; }
    50% { transform: translateY(-5px); opacity: 1; }
  }
  
  /* Suggestions */
  .helpbot-suggestions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 12px 16px;
    background: rgba(15, 23, 42, 0.9);
    border-top: 1px solid rgba(99, 102, 241, 0.1);
  }
  
  .suggestion-btn {
    padding: 8px 14px;
    border: 1px solid rgba(99, 102, 241, 0.3);
    background: rgba(99, 102, 241, 0.1);
    color: #a5b4fc;
    border-radius: 20px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .suggestion-btn:hover {
    background: rgba(99, 102, 241, 0.25);
    border-color: rgba(99, 102, 241, 0.5);
    transform: translateY(-2px);
  }
  
  /* Form */
  .helpbot-form {
    display: flex;
    gap: 10px;
    padding: 14px 16px;
    background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
    border-top: 1px solid rgba(99, 102, 241, 0.2);
  }
  
  .helpbot-input {
    flex: 1;
    padding: 12px 16px;
    border-radius: 25px;
    border: 1px solid rgba(99, 102, 241, 0.3);
    background: rgba(15, 23, 42, 0.8);
    color: #e5e7eb;
    outline: none;
    font-size: 13px;
    transition: all 0.2s;
  }
  
  .helpbot-input:focus {
    border-color: #6366f1;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
  }
  
  .helpbot-input::placeholder {
    color: #6b7280;
  }
  
  .helpbot-send {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    border: 0;
    cursor: pointer;
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
  }
  
  .helpbot-send:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
  }
  
  .helpbot-send:active {
    transform: scale(0.95);
  }
  
  /* Collapsed state */
  .helpbot.collapsed {
    width: auto;
    border-radius: 30px;
  }
  
  .helpbot.collapsed .helpbot-body,
  .helpbot.collapsed .helpbot-form,
  .helpbot.collapsed .helpbot-suggestions,
  .helpbot.collapsed .helpbot-subtitle {
    display: none;
  }
  
  .helpbot.collapsed .helpbot-header {
    padding: 12px 16px;
    border-radius: 30px;
  }
  
  /* Mobile responsiveness */
  @media (max-width: 480px) {
    .helpbot {
      right: 12px;
      bottom: 12px;
      width: calc(100vw - 24px);
    }
    
    .helpbot-body {
      height: 250px;
    }
  }
</style>

<script>
  (function(){
    const bot = document.getElementById("helpbot");
    const toggle = document.getElementById("helpbot-toggle");
    const body = document.getElementById("helpbot-body");
    const form = document.getElementById("helpbot-form");
    const input = document.getElementById("helpbot-input");
    const suggestions = document.getElementById("helpbot-suggestions");

    // Toggle collapse
    toggle.addEventListener("click", () => {
      bot.classList.toggle("collapsed");
      toggle.textContent = bot.classList.contains("collapsed") ? "+" : "−";
    });

    // Format markdown-like text
    function formatResponse(text) {
      return text
        .replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>')
        .replace(/\\\\n/g, '<br>')
        .replace(/\\n/g, '<br>')
        .replace(/• /g, '&bull; ');
    }

    function addMsg(text, who){
      const div = document.createElement("div");
      div.className = "helpbot-msg " + who;
      
      if (who === "user") {
        div.innerHTML = '<div class="user-content">' + text + '</div>';
      } else {
        div.innerHTML = '<div class="bot-avatar">🤖</div><div class="bot-content">' + formatResponse(text) + '</div>';
      }
      
      body.appendChild(div);
      body.scrollTop = body.scrollHeight;
    }

    function addTypingIndicator() {
      const div = document.createElement("div");
      div.className = "helpbot-msg bot";
      div.id = "typing-indicator";
      div.innerHTML = `
        <div class="bot-avatar">🤖</div>
        <div class="bot-content">
          <div class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      `;
      body.appendChild(div);
      body.scrollTop = body.scrollHeight;
    }

    function removeTypingIndicator() {
      const indicator = document.getElementById("typing-indicator");
      if (indicator) indicator.remove();
    }

    function getCSRFToken(){
      const tokenInput = form.querySelector("input[name='csrfmiddlewaretoken']");
      return tokenInput ? tokenInput.value : "";
    }

    async function sendMessage(msg) {
      if (!msg.trim()) return;
      
      addMsg(msg, "user");
      input.value = "";
      input.disabled = true;
      
      // Hide suggestions after first message
      if (suggestions) {
        suggestions.style.display = "none";
      }
      
      addTypingIndicator();

      try {
        const res = await fetch("{% url 'teacher_help_bot' %}", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
          },
          body: JSON.stringify({ message: msg })
        });

        removeTypingIndicator();
        const data = await res.json();
        addMsg(data.reply || "Sorry — I didn't understand. Try asking differently.", "bot");
      } catch(err) {
        removeTypingIndicator();
        addMsg("⚠️ Connection error. Please try again.", "bot");
      } finally {
        input.disabled = false;
        input.focus();
      }
    }

    // Form submit
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      sendMessage(input.value);
    });

    // Suggestion buttons
    document.querySelectorAll(".suggestion-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const question = btn.getAttribute("data-q");
        sendMessage(question);
      });
    });
  })();
</script>

{% endblock %}
'''

# Read the file
with open('quizzes/templates/quizzes/teacher_folders.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find start and end of the section
start_marker = '<!-- ✅ Teacher Help Bot Widget'
end_marker = '{% endblock %}'

start = content.find(start_marker)
end = content.find(end_marker)

if start == -1:
    print("ERROR: Could not find start marker")
elif end == -1:
    print("ERROR: Could not find end marker")
else:
    # Replace the section
    new_content = content[:start] + NEW_HELPBOT_UI
    
    with open('quizzes/templates/quizzes/teacher_folders.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("SUCCESS: Updated teacher help bot UI!")
    print(f"Replaced from position {start} to {end}")
