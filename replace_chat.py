import re

with open('templates/advisor/chat.html', 'r') as f:
    content = f.read()

# 1. Update the layout
layout_replacement = """
<div class="chat-layout" style="display: grid; grid-template-columns: 250px 1fr 300px; gap: var(--space-4); height: 100%;">
    
    <!-- Chat History Sidebar -->
    <div class="chat-history-sidebar card" style="display: flex; flex-direction: column; overflow: hidden; height: calc(100vh - 120px); position: sticky; top: 100px;">
        <div class="card-header" style="background: rgba(0,0,0,0.02); display: flex; justify-content: space-between; align-items: center;">
            <strong style="font-size: 0.875rem; color: var(--color-text-muted); text-transform: uppercase;">Chat History</strong>
        </div>
        <div style="padding: var(--space-3);">
            <button type="button" id="newChatBtn" class="btn btn-primary" style="width: 100%; justify-content: center; margin-bottom: var(--space-3);">
                + New Chat
            </button>
        </div>
        <div id="historyList" style="flex: 1; overflow-y: auto; padding: 0 var(--space-3) var(--space-3) var(--space-3); display: flex; flex-direction: column; gap: var(--space-2);">
            <!-- History items will be populated here -->
        </div>
    </div>

    <!-- Main Chat Area -->
    <div class="chat-main card" style="height: calc(100vh - 120px); display: flex; flex-direction: column;">
"""
content = content.replace('<div class="chat-layout">\n    <!-- Main Chat Area -->\n    <div class="chat-main card">', layout_replacement)

# 2. Add Microphone and Language Selector to input area
input_area_replacement = """
        <div style="padding: var(--space-4); border-top: 1px solid var(--color-border); background: var(--color-surface);">
            <form id="chatForm" class="chat-input-area" style="display: flex; gap: var(--space-2);">
                {% csrf_token %}
                <input type="text" id="queryInput" placeholder="Ask an academic question..." required style="flex: 1;">
                
                <select id="voiceLang" class="form-control" style="width: auto; padding: 0 0.5rem;">
                    <option value="en-IN">English</option>
                    <option value="hi-IN">Hindi</option>
                    <option value="pa-IN">Punjabi</option>
                    <option value="ta-IN">Tamil</option>
                    <option value="te-IN">Telugu</option>
                    <option value="bn-IN">Bengali</option>
                    <option value="mr-IN">Marathi</option>
                    <option value="gu-IN">Gujarati</option>
                    <option value="kn-IN">Kannada</option>
                    <option value="ml-IN">Malayalam</option>
                    <option value="or-IN">Odia</option>
                    <option value="as-IN">Assamese</option>
                    <option value="ur-IN">Urdu</option>
                    <option value="ne-NP">Nepali</option>
                </select>
                
                <button type="button" id="micBtn" class="btn btn-secondary" style="padding: 0 0.75rem;" title="Voice Input">
                    🎤
                </button>
                
                <button type="submit" id="sendBtn" class="btn btn-primary" style="min-width: 100px;">
                    <span id="sendText">Send</span>
                    <svg id="loadingSpinner" style="width: 20px; height: 20px; display: none; animation: spin 1s linear infinite;" fill="none" viewBox="0 0 24 24"><circle style="opacity: 0.25;" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path style="opacity: 0.75;" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                </button>
            </form>
            <div id="voiceStatus" style="font-size: 0.75rem; color: var(--color-text-muted); margin-top: 0.25rem; display: none;"></div>
        </div>
"""
# Replace the existing input area
old_input = """        <div style="padding: var(--space-4); border-top: 1px solid var(--color-border); background: var(--color-surface);">
            <form id="chatForm" class="chat-input-area">
                {% csrf_token %}
                <input type="text" id="queryInput" placeholder="Ask an academic question..." required>
                <button type="submit" id="sendBtn" class="btn btn-primary" style="min-width: 100px;">
                    <span id="sendText">Send</span>
                    <svg id="loadingSpinner" style="width: 20px; height: 20px; display: none; animation: spin 1s linear infinite;" fill="none" viewBox="0 0 24 24"><circle style="opacity: 0.25;" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path style="opacity: 0.75;" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                </button>
            </form>
        </div>"""
content = content.replace(old_input, input_area_replacement)

# 3. Add JS for Voice, History, and currentSessionId
js_additions = """
    let currentSessionId = null;
    const voiceStatus = document.getElementById('voiceStatus');
    const micBtn = document.getElementById('micBtn');
    const voiceLang = document.getElementById('voiceLang');
    const historyList = document.getElementById('historyList');
    
    // Voice Recognition Setup
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;
    
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        
        recognition.onstart = function() {
            voiceStatus.textContent = "Listening...";
            voiceStatus.style.display = "block";
            micBtn.style.background = "#fca5a5";
        };
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            document.getElementById('queryInput').value = transcript;
            voiceStatus.style.display = "none";
            micBtn.style.background = "";
        };
        
        recognition.onerror = function(event) {
            voiceStatus.textContent = "Voice error: " + event.error;
            voiceStatus.style.display = "block";
            micBtn.style.background = "";
            setTimeout(() => { voiceStatus.style.display = "none"; }, 3000);
        };
        
        recognition.onend = function() {
            voiceStatus.style.display = "none";
            micBtn.style.background = "";
        };
        
        micBtn.addEventListener('click', () => {
            recognition.lang = voiceLang.value;
            recognition.start();
        });
    } else {
        micBtn.style.display = 'none';
        voiceLang.style.display = 'none';
        voiceStatus.textContent = "Voice input is not supported in this browser.";
        voiceStatus.style.display = "block";
    }

    // Load Chat History
    async function loadChatHistory() {
        const studentId = document.getElementById('student_id') ? document.getElementById('student_id').value : '';
        try {
            const res = await fetch(`/advisor/chat/history/?student_id=${studentId}`);
            const data = await res.json();
            historyList.innerHTML = '';
            if (data.sessions.length === 0) {
                historyList.innerHTML = '<div style="color: var(--color-text-muted); font-size: 0.8rem; text-align: center; margin-top: 1rem;">No previous chats</div>';
                return;
            }
            data.sessions.forEach(s => {
                const btn = document.createElement('button');
                btn.className = 'btn';
                btn.style.cssText = 'width: 100%; text-align: left; padding: 0.5rem; justify-content: flex-start; font-size: 0.85rem; background: var(--color-surface); border: 1px solid var(--color-border); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;';
                if (currentSessionId === s.id) {
                    btn.style.borderColor = 'var(--color-primary)';
                    btn.style.background = 'var(--color-primary-light)';
                    btn.style.color = 'white';
                }
                btn.textContent = s.title;
                btn.onclick = () => loadSession(s.id);
                historyList.appendChild(btn);
            });
        } catch (e) {
            console.error("Failed to load history", e);
        }
    }
    
    // Load specific session
    async function loadSession(id) {
        currentSessionId = id;
        document.getElementById('evidencePanel').innerHTML = `<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; opacity: 0.6;">
            <p style="font-size: 0.875rem; text-align: center;">Evidence panel reset.</p>
        </div>`;
        document.getElementById('stateIndicator').textContent = "LOADED";
        document.getElementById('stateIndicator').className = "badge badge-neutral";
        
        const chatHistoryDiv = document.getElementById('chatHistory');
        chatHistoryDiv.innerHTML = '<div style="text-align:center; padding: 2rem;"><svg style="width: 24px; height: 24px; animation: spin 1s linear infinite;" fill="none" viewBox="0 0 24 24"><circle style="opacity: 0.25;" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path style="opacity: 0.75;" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg></div>';
        
        loadChatHistory(); // refresh selection styling
        
        try {
            const res = await fetch(`/advisor/chat/messages/${id}/`);
            const data = await res.json();
            chatHistoryDiv.innerHTML = '';
            
            data.messages.forEach(msg => {
                if (msg.role === 'user') {
                    chatHistoryDiv.innerHTML += `
                        <div class="message msg-user">
                            <p>${msg.content.text}</p>
                        </div>
                    `;
                } else {
                    renderAssistantMessage(msg.content, chatHistoryDiv, false);
                }
            });
            chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
        } catch (e) {
            console.error("Failed to load messages", e);
            chatHistoryDiv.innerHTML = '<div class="message msg-bot"><p>Error loading messages.</p></div>';
        }
    }
    
    // New Chat Button
    document.getElementById('newChatBtn').addEventListener('click', () => {
        currentSessionId = null;
        loadChatHistory();
        const chatHistoryDiv = document.getElementById('chatHistory');
        chatHistoryDiv.innerHTML = `
            <div class="message msg-bot">
                <p style="font-weight: 500;">Hello! I am the AI Academic Advisor.</p>
                <p style="font-size: 0.875rem; color: var(--color-text-muted); margin-top: var(--space-2);">Ask me questions about courses, prerequisites, rules, or select a Demo student profile from the top right to ask personalized eligibility questions.</p>
            </div>
        `;
        document.getElementById('evidencePanel').innerHTML = `<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; opacity: 0.6;">
            <p style="font-size: 0.875rem; text-align: center;">Ask a question to see retrieved official sources and decision metadata.</p>
        </div>`;
        document.getElementById('stateIndicator').textContent = "WAITING";
        document.getElementById('stateIndicator').className = "badge badge-neutral";
    });
    
    // Reusable render function for assistant messages
    function renderAssistantMessage(data, container, updateEvidence = true) {
        let badgeClass = "badge badge-neutral";
        let stateStyle = "";
        if (data.state === 'ELIGIBLE') { badgeClass = 'badge badge-success'; stateStyle = "background: #d1fae5; color: #065f46; border-color: #34d399;"; }
        else if (data.state === 'NOT_ELIGIBLE') { badgeClass = 'badge badge-danger'; stateStyle = "background: #fee2e2; color: #991b1b; border-color: #f87171;"; }
        else if (data.state === 'NEEDS_MORE_INFORMATION') { badgeClass = 'badge badge-warning'; stateStyle = "background: #fef3c7; color: #92400e; border-color: #fbbf24;"; }
        else if (data.state === 'CONFLICTING_INFORMATION') { badgeClass = 'badge badge-warning'; stateStyle = "background: #ffedd5; color: #9a3412; border-color: #fdba74;"; }
        else { badgeClass = 'badge badge-neutral'; stateStyle = "background: #f1f5f9; color: #334155; border-color: #cbd5e1;"; }
        
        let contentHtml = `<div style="margin-top: 0.5rem; line-height: 1.5; font-size: 0.95rem; white-space: pre-wrap;">${data.answer}</div>`;
        
        if (data.reason) {
            contentHtml += `
                <div style="margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid var(--color-border);">
                    <span style="font-size: 0.7rem; font-weight: 700; color: var(--color-text-muted); text-transform: uppercase;">Reasoning</span>
                    <div style="font-size: 0.875rem; color: var(--color-text-muted); margin-top: 0.25rem;">${data.reason}</div>
                </div>`;
        }
        if (data.missing_information && data.missing_information.length > 0) {
            contentHtml += `
                <div style="margin-top: 0.75rem; background: #fffbeb; border: 1px solid #fde68a; padding: 0.75rem; border-radius: var(--radius-md);">
                    <span style="font-size: 0.7rem; font-weight: 700; color: #b45309; text-transform: uppercase;">Missing Information</span>
                    <ul style="font-size: 0.875rem; color: #92400e; margin-left: 1rem; margin-top: 0.25rem;">
                        ${data.missing_information.map(item => `<li>${item}</li>`).join('')}
                    </ul>
                </div>`;
        }
        if (data.recommendation) {
            contentHtml += `
                <div style="margin-top: 0.75rem; background: #ecfdf5; border: 1px solid #a7f3d0; padding: 0.75rem; border-radius: var(--radius-md);">
                    <span style="font-size: 0.7rem; font-weight: 700; color: #047857; text-transform: uppercase;">Recommendation</span>
                    <div style="font-size: 0.875rem; color: #065f46; margin-top: 0.25rem;">${data.recommendation}</div>
                </div>`;
        }
        
        container.innerHTML += `
            <div class="message msg-bot">
                <span class="state-badge" style="${stateStyle}">${data.state}</span>
                ${contentHtml}
            </div>
        `;
        
        if (updateEvidence) {
            document.getElementById('stateIndicator').textContent = data.state;
            document.getElementById('stateIndicator').className = badgeClass;
            
            const evidencePanel = document.getElementById('evidencePanel');
            evidencePanel.innerHTML = '';
            if (data.evidence && data.evidence.length > 0) {
                data.evidence.forEach((ev, i) => {
                    if (typeof ev === 'string') {
                        evidencePanel.innerHTML += `
                            <div class="evidence-item">
                                <h4 style="display: flex; align-items: center; gap: 0.5rem;"><span style="background: var(--color-border); width: 20px; height: 20px; display: inline-flex; align-items: center; justify-content: center; border-radius: 50%; font-size: 0.6rem;">${i+1}</span> Source Content</h4>
                                <p>${ev}</p>
                            </div>
                        `;
                    } else {
                        evidencePanel.innerHTML += `
                            <div class="evidence-item">
                                <h4 style="display: flex; align-items: center; gap: 0.5rem;"><span style="background: var(--color-border); width: 20px; height: 20px; display: inline-flex; align-items: center; justify-content: center; border-radius: 50%; font-size: 0.6rem;">${i+1}</span> <span style="background: var(--color-primary-light); color: white; padding: 2px 6px; border-radius: 4px;">${ev.source}</span></h4>
                                ${ev.page ? `<p style="font-weight: 600; color: var(--color-text-main); margin-top: 0.5rem;">Location: ${ev.page}</p>` : ''}
                                <p class="truncate-3-lines">${ev.content}</p>
                            </div>
                        `;
                    }
                });
            } else {
                evidencePanel.innerHTML = `
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; opacity: 0.6;">
                        <svg style="width: 48px; height: 48px; color: var(--color-border); margin-bottom: var(--space-3);" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                        <p style="font-size: 0.875rem; text-align: center;">No specific institutional sources were retrieved for this query.</p>
                    </div>`;
            }
        }
    }
    
    // Initial Load
    document.addEventListener('DOMContentLoaded', loadChatHistory);
    
    // Hook student change to reload history
    const studentSelect = document.getElementById('student_id');
    if (studentSelect) {
        studentSelect.addEventListener('change', () => {
            currentSessionId = null;
            loadChatHistory();
            document.getElementById('newChatBtn').click();
        });
    }
"""

# 4. Modify the chat form submission
# We need to append session_id to formData and use the reusable renderAssistantMessage
submit_replacement_find = """            if (studentId) formData.append('student_id', studentId);"""
submit_replacement_replace = """            if (studentId) formData.append('student_id', studentId);
            if (currentSessionId) formData.append('session_id', currentSessionId);"""

content = content.replace(submit_replacement_find, submit_replacement_replace)

render_find = """            // Render State
            let badgeClass = "badge badge-neutral";
            let stateStyle = "";"""
render_end = """                        <p style="font-size: 0.875rem; text-align: center;">No specific institutional sources were retrieved for this query.</p>
                    </div>`;
            }"""

render_regex = re.compile(re.escape(render_find) + r'.*?' + re.escape(render_end), re.DOTALL)
render_replace = """            if (data.session_id && !currentSessionId) {
                currentSessionId = data.session_id;
                loadChatHistory();
            }
            renderAssistantMessage(data, chatHistory, true);
            chatHistory.scrollTop = chatHistory.scrollHeight;"""

content = render_regex.sub(render_replace, content)

# 5. Insert JS additions before the final closing script tag
content = content.replace('    // Auto-submit if \'q\' is in URL', js_additions + '\n    // Auto-submit if \'q\' is in URL')

with open('templates/advisor/chat.html', 'w') as f:
    f.write(content)

