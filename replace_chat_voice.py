import re

with open('templates/advisor/chat.html', 'r') as f:
    content = f.read()

# 1. Remove the language dropdown entirely
lang_dropdown_pattern = re.compile(r'<select id="voiceLang".*?</select>', re.DOTALL)
content = lang_dropdown_pattern.sub('', content)

# 2. Update the Mic button slightly (we'll keep the text 🎙️ as SVG or emoji, user said SVG/existing if possible, but keeping 🎙️ is fine if styled well, the prompt says "Replace the current small/basic microphone icon with a clear professional microphone button... preferably SVG. Do NOT use emoji if proper icon available."
# Let's replace the emoji with a nice SVG microphone icon.
mic_svg = """<svg xmlns="http://www.w3.org/2000/svg" style="width: 20px; height: 20px; margin-right: 4px; vertical-align: middle;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>"""

mic_button_old = """<button type="button" id="micBtn" class="btn btn-secondary" style="padding: 0 0.75rem;" title="Voice Input">
                    🎤
                </button>"""
mic_button_new = f"""<button type="button" id="micBtn" class="btn btn-secondary" style="padding: 0 0.75rem; display: flex; align-items: center;" title="Voice Input">
                    {mic_svg}
                </button>"""
content = content.replace(mic_button_old, mic_button_new)

# 3. Update the JavaScript for SpeechRecognition
js_old_pattern = re.compile(r'    // Voice Recognition Setup.*?\}\n', re.DOTALL)

js_new = """    // Voice Recognition Setup
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;
    let isListening = false;
    let finalTranscript = '';
    
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        
        recognition.onstart = function() {
            isListening = true;
            voiceStatus.textContent = "Listening...";
            voiceStatus.style.display = "block";
            micBtn.style.background = "#fca5a5";
            finalTranscript = document.getElementById('queryInput').value;
            if (finalTranscript.length > 0 && !finalTranscript.endsWith(' ')) {
                finalTranscript += ' ';
            }
        };
        
        recognition.onresult = function(event) {
            let interimTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript + ' ';
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }
            document.getElementById('queryInput').value = finalTranscript + interimTranscript;
        };
        
        recognition.onerror = function(event) {
            voiceStatus.textContent = "Voice error: " + event.error;
            voiceStatus.style.display = "block";
            micBtn.style.background = "";
            isListening = false;
            setTimeout(() => { voiceStatus.style.display = "none"; }, 3000);
        };
        
        recognition.onend = function() {
            voiceStatus.style.display = "none";
            micBtn.style.background = "";
            isListening = false;
            document.getElementById('queryInput').value = finalTranscript.trim();
        };
        
        micBtn.addEventListener('click', () => {
            if (isListening) {
                recognition.stop();
            } else {
                try {
                    recognition.start();
                } catch(e) {
                    console.error("Speech recognition error", e);
                }
            }
        });
    } else {
        micBtn.style.display = 'none';
        voiceStatus.textContent = "Voice input is not supported in this browser.";
        voiceStatus.style.display = "block";
    }
"""
content = js_old_pattern.sub(js_new, content)
# Also remove `const voiceLang = document.getElementById('voiceLang');`
content = content.replace("const voiceLang = document.getElementById('voiceLang');", "")

with open('templates/advisor/chat.html', 'w') as f:
    f.write(content)
