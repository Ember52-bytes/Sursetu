/**
 * PALASH Setu - High Performance Web Application Logic
 * Integrates:
 *   1. Real-Time Streaming ASR (Web Speech API + Vosk Offline Hardware Mic)
 *   2. Instant Multi-Script Machine Translation (Ol Chiki ᱚᱞ ᱪᱤᱠᱤ & Odia Script ଓଡ଼ିଆ)
 *   3. Santali vs Odia Script Classifier (LID - Mayurbhanj Edition)
 *   4. Multi-Script Transducer (Ol Chiki ⇄ Odia ⇄ Devanagari)
 *   5. Primary Education Vocabulary Bank & Worksheet Studio
 */

document.addEventListener('DOMContentLoaded', () => {
    // ------------------------------------------------------------------
    // 1. Navigation Tab Switching
    // ------------------------------------------------------------------
    const navBtns = document.querySelectorAll('.nav-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            navBtns.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));

            btn.classList.add('active');
            const targetPaneId = btn.getAttribute('data-tab');
            const targetPane = document.getElementById(targetPaneId);
            if (targetPane) {
                targetPane.classList.add('active');
            }
        });
    });

    // ------------------------------------------------------------------
    // 2. High-Performance Real-Time Audio Engine & Visualizer
    // ------------------------------------------------------------------
    const canvas = document.getElementById('audio-wave-canvas');
    const ctx = canvas ? canvas.getContext('2d') : null;
    const recordBtn = document.getElementById('record-btn');
    const micStatusLabel = document.getElementById('mic-status-label');
    const liveTextStream = document.getElementById('live-text-stream');
    const asrHindiOutput = document.getElementById('asr-hindi-output');
    const mtTargetOutput = document.getElementById('mt-target-output');
    const targetLangAsr = document.getElementById('target-lang-asr');

    let isRecording = false;
    let audioCtx = null;
    let analyser = null;
    let microphoneStream = null;
    let animFrameId = null;

    // Fast In-Memory Translation Cache
    const TRANSLATION_CACHE = new Map();

    // Web Speech API Continuous Recognition Setup
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;

    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.maxAlternatives = 1;
        recognition.lang = 'hi-IN';

        recognition.onstart = () => {
            if (micStatusLabel) micStatusLabel.textContent = '🎙️ Live Streaming... Speak continuously in Hindi';
        };

        recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                const text = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += text;
                } else {
                    interimTranscript += text;
                }
            }

            const currentSpoken = (interimTranscript || finalTranscript).trim();
            if (currentSpoken) {
                const targetCode = targetLangAsr ? targetLangAsr.value : 'sat_Olck';
                const liveTranslated = instantTranslate(currentSpoken, 'hin_Deva', targetCode);
                const displayClass = targetCode === 'sat_Orya' ? 'odia-display' : 'ol-chiki-display';
                
                if (liveTextStream) {
                    liveTextStream.innerHTML = `🎙️ <strong>${currentSpoken}</strong> ➔ 🌐 <span class="${displayClass}" style="font-weight:700; color: #38BDF8;">${liveTranslated}</span>`;
                }
                if (asrHindiOutput) {
                    asrHindiOutput.innerHTML = `<div>${currentSpoken}</div>`;
                }
                if (mtTargetOutput) {
                    mtTargetOutput.className = `output-content ${displayClass}`;
                    mtTargetOutput.innerHTML = `<div>${liveTranslated}</div>`;
                }
            }

            if (finalTranscript.trim()) {
                appendAsrResult(finalTranscript.trim());
            }
        };

        recognition.onerror = (event) => {
            if (event.error !== 'no-speech' && event.error !== 'aborted') {
                console.warn('Speech recognition warning:', event.error);
                if (micStatusLabel && isRecording) {
                    micStatusLabel.textContent = `🎙️ Listening active (Offline Vosk backup running)`;
                }
            }
        };

        recognition.onend = () => {
            if (isRecording) {
                try { recognition.start(); } catch (e) {}
            }
        };
    }

    // Toggle Microphone Recording
    if (recordBtn) {
        recordBtn.addEventListener('click', () => {
            if (!isRecording) {
                startRecording();
            } else {
                stopRecording();
            }
        });
    }

    async function startRecording() {
        isRecording = true;
        if (recordBtn) recordBtn.classList.add('recording');
        if (micStatusLabel) micStatusLabel.textContent = '🎙️ Real-Time Listening ON... Speak in Hindi';
        if (liveTextStream) liveTextStream.textContent = '⏳ Listening live... Speak Hindi words (e.g. नमस्ते शिक्षक, किताब खोलो)';

        // 1. Audio Canvas Visualizer with Web Audio API
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            microphoneStream = stream;
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioCtx.createAnalyser();
            analyser.fftSize = 128;
            analyser.smoothingTimeConstant = 0.8;
            const source = audioCtx.createMediaStreamSource(stream);
            source.connect(analyser);
            drawHighDefEqualizer();
        } catch (e) {
            console.warn('Microphone Web Audio visualizer access skipped:', e);
        }

        // 2. Start Real-time Continuous Web Speech Recognition
        if (recognition) {
            try {
                recognition.start();
            } catch (e) {}
        }

        // 3. Parallel Hardware Vosk Polling as Fallback
        pollVoskHardwareMic();
    }

    async function pollVoskHardwareMic() {
        if (!isRecording) return;
        try {
            const targetLang = targetLangAsr ? targetLangAsr.value : 'sat_Olck';
            const response = await fetch('/api/asr/record_hardware_mic', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ duration: 3.0, target_lang: targetLang })
            });

            if (response.ok && isRecording) {
                const data = await response.json();
                if (data.hindi_text && data.hindi_text.trim()) {
                    appendAsrResult(data.hindi_text.trim());
                }
            }
        } catch (err) {
            console.warn('Vosk hardware mic loop status:', err);
        }

        if (isRecording) {
            setTimeout(pollVoskHardwareMic, 400);
        }
    }

    function stopRecording() {
        isRecording = false;
        if (recordBtn) recordBtn.classList.remove('recording');
        if (micStatusLabel) micStatusLabel.textContent = 'Click Microphone to Start Listening';

        if (recognition) {
            try { recognition.stop(); } catch (e) {}
        }

        if (audioCtx) {
            try { audioCtx.close(); } catch (e) {}
            audioCtx = null;
        }

        if (microphoneStream) {
            microphoneStream.getTracks().forEach(track => track.stop());
            microphoneStream = null;
        }

        if (animFrameId) {
            cancelAnimationFrame(animFrameId);
        }

        if (ctx && canvas) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
    }

    // High Definition Glowing Spectrum Visualizer
    function drawHighDefEqualizer() {
        if (!analyser || !ctx || !canvas) return;

        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        function render() {
            if (!isRecording) return;
            animFrameId = requestAnimationFrame(render);
            analyser.getByteFrequencyData(dataArray);

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            const numBars = 36;
            const barWidth = (canvas.width / numBars) - 3;
            const step = Math.floor(bufferLength / numBars);

            for (let i = 0; i < numBars; i++) {
                const value = dataArray[i * step] || 0;
                const percent = value / 255;
                const barHeight = Math.max(4, percent * canvas.height * 0.88);
                const x = i * (barWidth + 3);
                const y = canvas.height - barHeight;

                const gradient = ctx.createLinearGradient(0, canvas.height, 0, y);
                gradient.addColorStop(0, '#10B981');
                gradient.addColorStop(0.5, '#6366F1');
                gradient.addColorStop(1, '#EC4899');

                ctx.fillStyle = gradient;
                ctx.beginPath();
                ctx.roundRect(x, y, barWidth, barHeight, [3, 3, 0, 0]);
                ctx.fill();

                // Glowing peak dot
                if (barHeight > 10) {
                    ctx.fillStyle = '#FFFFFF';
                    ctx.fillRect(x, y - 3, barWidth, 2);
                }
            }
        }
        render();
    }

    async function appendAsrResult(hindiText) {
        if (liveTextStream) liveTextStream.textContent = `✓ Recognized: "${hindiText}"`;
        if (asrHindiOutput) asrHindiOutput.innerHTML = `<div>${hindiText}</div>`;

        const targetCode = targetLangAsr ? targetLangAsr.value : 'sat_Olck';
        const translation = await fetchTranslation(hindiText, 'hin_Deva', targetCode);

        const displayClass = targetCode === 'sat_Orya' ? 'odia-display' : 'ol-chiki-display';
        if (mtTargetOutput) {
            mtTargetOutput.className = `output-content ${displayClass}`;
            mtTargetOutput.innerHTML = `<div>${translation}</div>`;
        }
    }

    // Fast instant translation with caching and multi-word sliding window
    function instantTranslate(text, src, tgt) {
        const cacheKey = `${src}_${tgt}_${text}`;
        if (TRANSLATION_CACHE.has(cacheKey)) {
            return TRANSLATION_CACHE.get(cacheKey);
        }

        const res = fallbackClientTranslate(text, src, tgt);
        TRANSLATION_CACHE.set(cacheKey, res);
        return res;
    }

    // Quick Prompt Chips
    const promptChips = document.querySelectorAll('.prompt-chip');
    promptChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const phrase = chip.getAttribute('data-phrase');
            if (phrase) {
                appendAsrResult(phrase);
            }
        });
    });

    // Copy buttons
    const copyHindiBtn = document.getElementById('copy-hindi-btn');
    if (copyHindiBtn) {
        copyHindiBtn.addEventListener('click', () => {
            const text = asrHindiOutput ? asrHindiOutput.innerText : '';
            if (text) {
                navigator.clipboard.writeText(text);
                copyHindiBtn.textContent = '✓';
                setTimeout(() => copyHindiBtn.textContent = '📋', 1200);
            }
        });
    }

    const copyTargetBtn = document.getElementById('copy-target-btn');
    if (copyTargetBtn) {
        copyTargetBtn.addEventListener('click', () => {
            const text = mtTargetOutput ? mtTargetOutput.innerText : '';
            if (text) {
                navigator.clipboard.writeText(text);
                copyTargetBtn.textContent = '✓';
                setTimeout(() => copyTargetBtn.textContent = '📋', 1200);
            }
        });
    }

    // TTS audio playback
    const ttsBtn = document.getElementById('tts-btn');
    if (ttsBtn) {
        ttsBtn.addEventListener('click', () => {
            const text = mtTargetOutput ? mtTargetOutput.innerText : '';
            if ('speechSynthesis' in window && text) {
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.rate = 0.9;
                window.speechSynthesis.speak(utterance);
            }
        });
    }

    // ------------------------------------------------------------------
    // 3. Translation Hub Logic
    // ------------------------------------------------------------------
    const mtInputText = document.getElementById('mt-input-text');
    const mtResultText = document.getElementById('mt-result-text');
    const mtSrcLang = document.getElementById('mt-src-lang');
    const mtTgtLang = document.getElementById('mt-tgt-lang');
    const translateBtn = document.getElementById('translate-btn');
    const clearMtBtn = document.getElementById('clear-mt-btn');
    const swapLangsBtn = document.getElementById('swap-langs');
    const charNum = document.getElementById('char-num');
    const mtLatency = document.getElementById('mt-latency');
    const mtConfidenceBadge = document.getElementById('mt-confidence-badge');
    const mtModeBadge = document.getElementById('mt-mode-badge');

    const learnHindiInput = document.getElementById('learn-hindi-input');
    const learnSantaliInput = document.getElementById('learn-santali-input');
    const learnTargetScript = document.getElementById('learn-target-script');
    const learnSubmitBtn = document.getElementById('learn-submit-btn');
    const learnFeedbackMsg = document.getElementById('learn-feedback-msg');

    const mtVoiceBtn = document.getElementById('mt-voice-btn');
    const learnVoiceBtn = document.getElementById('learn-voice-btn');

    if (mtInputText) {
        mtInputText.addEventListener('input', () => {
            if (charNum) charNum.textContent = mtInputText.value.length;
            // Real-time translation as user types
            const txt = mtInputText.value.trim();
            if (txt.length > 1) {
                const targetCode = mtTgtLang ? mtTgtLang.value : 'sat_Olck';
                const liveRes = instantTranslate(txt, mtSrcLang ? mtSrcLang.value : 'hin_Deva', targetCode);
                const displayClass = targetCode === 'sat_Orya' ? 'odia-display' : 'ol-chiki-display';
                if (mtResultText) {
                    mtResultText.className = `mt-result-area ${displayClass}`;
                    mtResultText.innerHTML = `<div>${liveRes}</div>`;
                }
            }
        });
    }

    if (mtTgtLang && mtResultText) {
        mtTgtLang.addEventListener('change', () => {
            if (mtTgtLang.value === 'sat_Orya') {
                mtResultText.className = 'mt-result-area odia-display';
            } else {
                mtResultText.className = 'mt-result-area ol-chiki-display';
            }
            if (mtInputText && mtInputText.value.trim()) {
                if (translateBtn) translateBtn.click();
            }
        });
    }

    // Voice Input for Translation Hub
    if (mtVoiceBtn) {
        mtVoiceBtn.addEventListener('click', async () => {
            mtVoiceBtn.innerHTML = '🎙️ Speak Now (3s)...';
            mtVoiceBtn.style.background = 'var(--rose-accent)';
            mtVoiceBtn.style.color = '#fff';

            if (SpeechRecognition) {
                try {
                    const singleRec = new SpeechRecognition();
                    singleRec.lang = 'hi-IN';
                    singleRec.onresult = (ev) => {
                        const txt = ev.results[0][0].transcript;
                        if (txt) {
                            mtInputText.value = txt;
                            if (charNum) charNum.textContent = txt.length;
                            if (translateBtn) translateBtn.click();
                        }
                    };
                    singleRec.start();
                } catch(e) {}
            }

            try {
                const response = await fetch('/api/asr/record_hardware_mic', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ duration: 3.5, target_lang: mtTgtLang ? mtTgtLang.value : 'sat_Olck' })
                });
                if (response.ok) {
                    const data = await response.json();
                    if (data.hindi_text && data.hindi_text.trim()) {
                        mtInputText.value = data.hindi_text.trim();
                        if (charNum) charNum.textContent = data.hindi_text.trim().length;
                        if (data.translated_text && mtResultText) {
                            mtResultText.innerHTML = `<div>${data.translated_text}</div>`;
                        }
                    }
                }
            } catch (err) {
                console.warn('Vosk recording error:', err);
            } finally {
                mtVoiceBtn.innerHTML = '<span class="icon">🎙️</span> Voice Input';
                mtVoiceBtn.style.background = '';
                mtVoiceBtn.style.color = '';
            }
        });
    }

    // Voice Input for Teaching Model
    if (learnVoiceBtn) {
        learnVoiceBtn.addEventListener('click', async () => {
            learnVoiceBtn.textContent = '⏳';
            try {
                const response = await fetch('/api/asr/record_hardware_mic', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ duration: 3.0, target_lang: 'sat_Olck' })
                });
                if (response.ok) {
                    const data = await response.json();
                    if (data.hindi_text && data.hindi_text.trim()) {
                        learnHindiInput.value = data.hindi_text.trim();
                    }
                }
            } catch (e) {} finally {
                learnVoiceBtn.textContent = '🎙️';
            }
        });
    }

    if (translateBtn) {
        translateBtn.addEventListener('click', async () => {
            const text = mtInputText.value.trim();
            if (!text) return;

            mtResultText.innerHTML = '<span class="placeholder-text">Translating...</span>';
            const startTime = performance.now();

            const src = mtSrcLang.value;
            const tgt = mtTgtLang.value;

            const res = await fetchTranslationData(text, src, tgt);
            const duration = (performance.now() - startTime).toFixed(1);

            const displayClass = tgt === 'sat_Orya' ? 'odia-display' : 'ol-chiki-display';
            mtResultText.className = `mt-result-area ${displayClass}`;
            mtResultText.innerHTML = `<div>${res.translated_text}</div>`;

            if (mtLatency) mtLatency.textContent = `Latency: ${duration} ms`;
            if (mtConfidenceBadge && res.confidence !== undefined) {
                mtConfidenceBadge.textContent = `Confidence: ${(res.confidence * 100).toFixed(0)}%`;
            }
            if (mtModeBadge && res.mode) {
                mtModeBadge.textContent = res.mode;
            }
        });
    }

    // Teach Model Handler
    if (learnSubmitBtn) {
        learnSubmitBtn.addEventListener('click', async () => {
            const hindi = learnHindiInput.value.trim();
            const santali = learnSantaliInput.value.trim();
            const tgtScript = learnTargetScript ? learnTargetScript.value : 'sat_Olck';

            if (!hindi || !santali) {
                if (learnFeedbackMsg) {
                    learnFeedbackMsg.innerHTML = '<span style="color: var(--rose-accent);">⚠️ Please enter both Hindi and Santali text.</span>';
                }
                return;
            }

            try {
                const response = await fetch('/api/learn', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ hindi, santali, tgt_lang: tgtScript })
                });
                const data = await response.json();
                if (data.success) {
                    if (!CLIENT_VOCAB['hin_Deva'][tgtScript]) {
                        CLIENT_VOCAB['hin_Deva'][tgtScript] = {};
                    }
                    CLIENT_VOCAB['hin_Deva'][tgtScript][hindi] = santali;

                    if (learnFeedbackMsg) {
                        learnFeedbackMsg.innerHTML = `<span style="color: var(--emerald-accent);">✓ Model successfully learned: <strong>${hindi}</strong> = <strong>${santali}</strong> (${tgtScript})</span>`;
                    }
                    learnHindiInput.value = '';
                    learnSantaliInput.value = '';
                }
            } catch (err) {
                if (learnFeedbackMsg) {
                    learnFeedbackMsg.innerHTML = `<span style="color: var(--rose-accent);">Error teaching model: ${err}</span>`;
                }
            }
        });
    }

    if (clearMtBtn) {
        clearMtBtn.addEventListener('click', () => {
            mtInputText.value = '';
            mtResultText.innerHTML = '<span class="placeholder-text">Translation result will be displayed here...</span>';
            if (charNum) charNum.textContent = '0';
        });
    }

    if (swapLangsBtn) {
        swapLangsBtn.addEventListener('click', () => {
            const temp = mtSrcLang.value;
            mtSrcLang.value = mtTgtLang.value;
            mtTgtLang.value = temp;
        });
    }

    async function fetchTranslationData(text, src, tgt) {
        try {
            const response = await fetch('/api/translate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, src, tgt })
            });
            if (response.ok) {
                const data = await response.json();
                return {
                    translated_text: data.translated_text || data.result,
                    confidence: data.confidence,
                    mode: data.mode
                };
            }
        } catch (e) {
            console.warn('API translate fallback:', e);
        }

        return {
            translated_text: fallbackClientTranslate(text, src, tgt),
            confidence: 0.95,
            mode: 'OFFLINE_JS_CACHE'
        };
    }

    async function fetchTranslation(text, src, tgt) {
        const res = await fetchTranslationData(text, src, tgt);
        return res.translated_text;
    }

    // Client-side Fallback Educational Dictionary with multi-word phrases & Odia script
    const CLIENT_VOCAB = {
        "hin_Deva": {
            "sat_Olck": {
                "नमस्ते": "ᱡᱚᱦᱟᱨ",
                "जोहार": "ᱡᱚᱦᱟᱨ",
                "सबको जोहार": "ᱥᱟᱱᱟᱢ ᱠᱚ ᱡᱚᱦᱟᱨ",
                "धन्यवाद": "ᱥᱟᱨᱦᱟᱣ",
                "आपका स्वागत है": "ᱥᱟᱹᱜᱩᱱ ᱫᱟᱨᱟᱢ",
                "स्वागत": "ᱥᱟᱹᱜᱩᱱ ᱫᱟᱨᱟᱢ",
                "शुभ प्रभात": "ᱥᱟᱹᱜᱩᱱ ᱥᱮᱛᱟᱜ",
                "शुभ रात्रि": "ᱥᱟᱹᱜᱩᱱ ᱧᱤᱸᱫᱟᱹ",
                "हाँ": "ᱦᱮᱸ",
                "नहीं": "ᱵᱟᱝ",
                "शिक्षक": "ᱢᱟᱪᱮᱛ",
                "अध्यापक": "ᱢᱟᱪᱮᱛ",
                "शिक्षिका": "ᱢᱟᱪᱮᱛᱟᱹᱱᱤ",
                "छात्र": "ᱪᱮᱛᱮᱫᱤᱭᱟᱹ",
                "विद्यार्थी": "ᱪᱮᱛᱮᱫᱤᱭᱟᱹ",
                "स्कूल": "ᱤᱛᱩᱱ ᱟᱥᱲᱟ",
                "विद्यालय": "ᱤᱛᱩᱱ ᱟᱥᱲᱟ",
                "किताब": "ᱯᱩᱛᱷᱤ",
                "पुस्तक": "ᱯᱩᱛᱷᱤ",
                "कलम": "ᱠᱚᱞᱚᱢ",
                "कापी": "ᱚᱞ ᱯᱩᱛᱷᱤ",
                "गणित": "ᱞᱮᱠᱷᱟ",
                "भाषा": "ᱯᱟᱹᱨᱥᱤ",
                "पानी": "ᱫᱟᱜ",
                "सूरज": "ᱥᱤᱝ ᱪᱟᱸᱫᱚ",
                "चांद": "ᱧᱤᱸᱫᱟᱹ ᱪᱟᱸᱫᱚ",
                "पेड़": "ᱫᱟᱨᱮ",
                "फूल": "ᱵᱟᱦᱟ",
                "फल": "ᱡᱚ",
                "घर": "ᱚᱲᱟᱜ",
                "गांव": "ᱟᱹᱛᱩ",
                "मां": "ᱟᱭᱳ",
                "माता": "ᱟᱭᱳ",
                "पिता": "ᱵᱟᱵᱟ",
                "बाप": "ᱵᱟᱵᱟ",
                "भाई": "ᱵᱚᱭᱦᱟ",
                "बहन": "ᱢᱤᱥᱤ",
                "बच्चा": "ᱜᱤᱫᱽᱨᱟᱹ",
                "दोस्त": "ᱜᱟᱛᱮ",
                "एक": "ᱢᱤᱫ (᱑)",
                "दो": "ᱵᱟᱨ (᱒)",
                "तीन": "ᱯᱮ (᱓)",
                "चार": "ᱯᱩᱱ (᱔)",
                "पांच": "ᱢᱚᱬᱮ (᱕)",
                "छह": "ᱛᱩᱨᱩᱭ (᱖)",
                "सात": "ᱮᱭᱟᱮ (᱗)",
                "आठ": "ᱤᱨᱟᱹᱞ (᱘)",
                "नौ": "ᱟᱨᱮ (᱙)",
                "दस": "ᱜᱮᱞ (᱑᱐)",
                "आज हम गणित पढ़ेंगे": "ᱛᱮᱦᱮᱧ ᱵᱚᱱ ᱞᱮᱠᱷᱟ ᱵᱚᱱ ᱯᱟᱲᱦᱟᱣᱟ",
                "किताब खोलो": "ᱯᱩᱛᱷᱤ ᱡᱷᱤᱡᱽ ᱢᱮ",
                "सब बैठ जाओ": "ᱥᱟᱱᱟᱢ ᱠᱚ ᱫᱩᱲᱩᱵ ᱯᱮ",
                "साफ लिखो": "ᱥᱟᱯᱷᱟ ᱚᱞ ᱢᱮ"
            },
            "sat_Orya": {
                "नमस्ते": "ଜୋହାର",
                "जोहार": "ଜୋହାର",
                "सबको जोहार": "ସାନାମ କୋ ଜୋହାର",
                "धन्यवाद": "ସାରହାଓ",
                "आपका स्वागत है": "ସାଗୁନ ଦାରାମ",
                "स्वागत": "ସାଗୁନ ଦାରାମ",
                "शुभ प्रभात": "ସାଗୁନ ସେତାଗ",
                "हाँ": "ହେଁ",
                "नहीं": "ବାଙ୍ଗ",
                "शिक्षक": "ମାଚେତ",
                "शिक्षिका": "ମାଚେତନି",
                "छात्र": "ଚେତେଦିୟା",
                "स्कूल": "ଇତୁନ ଆସଡ଼ା",
                "किताब": "ପୁଥି",
                "कलम": "କଲମ",
                "कापी": "ଅଲ ପୁଥି",
                "गणित": "ଲେଖା",
                "पानी": "ଦାଗ",
                "सूरज": "ସିଂ ଚାନ୍ଦୋ",
                "चांद": "ଞିନ୍ଦା ଚାନ୍ଦୋ",
                "पेड़": "ଦାରେ",
                "फूल": "ବାହା",
                "फल": "ଜୋ",
                "घर": "ଅଡ଼ାଗ",
                "गांव": "ଆତୁ / ଏତୁ",
                "मां": "ଆୟୋ",
                "पिता": "ବାବା",
                "भाई": "ବୟହା / ବୟହ",
                "बहन": "ମିସି",
                "बच्चा": "ଗିଦ୍ରା",
                "दोस्त": "ଗାତେ",
                "एक": "ମିଦ (୧)",
                "दो": "ବାର (୨)",
                "तीन": "ପେ (୩)",
                "चार": "ପୁନ (୪)",
                "पांच": "ମୋᱬେ (୫)",
                "छह": "ତୁରୁୟ (୬)",
                "सात": "ଏୟାଏ (୭)",
                "आठ": "ଇରାଲ (୮)",
                "नौ": "ଆରେ (୯)",
                "दस": "ଗେଲ (୧୦)",
                "आज हम गणित पढ़ेंगे": "ତେହେଞ୍ଜ ବୋନ ଲେଖା ବୋନ ପାଡ଼ହାୱା",
                "किताब खोलो": "ପୁଥି ଝିଜ ମେ",
                "सब बैठ जाओ": "ସାନାମ କୋ ଦୁଡ଼ୁବ ପେ",
                "साफ लिखो": "ସାଫା ଅଲ ମେ"
            },
            "eng_Latn": {
                "नमस्ते": "Hello / Greetings",
                "शिक्षक": "Teacher",
                "छात्र": "Student",
                "स्कूल": "School",
                "किताब": "Book",
                "कलम": "Pen",
                "पानी": "Water",
                "सूरज": "Sun"
            }
        }
    };

    function fallbackClientTranslate(text, src, tgt) {
        if (!CLIENT_VOCAB[src] || !CLIENT_VOCAB[src][tgt]) {
            return `[${tgt}: ${text}]`;
        }

        const map = CLIENT_VOCAB[src][tgt];
        const cleanText = text.trim();
        if (map[cleanText]) return map[cleanText];

        // Multi-word greedy sliding window matching
        const words = cleanText.split(/\s+/);
        const result = [];
        let i = 0;

        while (i < words.length) {
            let matched = false;
            for (let w = Math.min(4, words.length - i); w > 1; w--) {
                const phrase = words.slice(i, i + w).join(' ');
                const phraseClean = phrase.replace(/[।,!?]/g, '');
                if (map[phraseClean] || map[phrase]) {
                    result.push(map[phraseClean] || map[phrase]);
                    i += w;
                    matched = true;
                    break;
                }
            }
            if (!matched) {
                const single = words[i].replace(/[।,!?]/g, '');
                result.push(map[single] || words[i]);
                i++;
            }
        }

        return result.join(' ');
    }

    // ------------------------------------------------------------------
    // 4. Script & Dialect LID Classifier & Transducer Logic
    // ------------------------------------------------------------------
    const lidInputText = document.getElementById('lid-input-text');
    const lidClassifyBtn = document.getElementById('lid-classify-btn');
    const lidResultBox = document.getElementById('lid-result-box');
    const lidDetectedLang = document.getElementById('lid-detected-lang');
    const lidConfidencePill = document.getElementById('lid-confidence-pill');
    const lidExplanation = document.getElementById('lid-explanation');
    const lidMarkersList = document.getElementById('lid-markers-list');
    const lidSampleBtns = document.querySelectorAll('.lid-sample-btn');

    const transduceSrcScript = document.getElementById('transduce-src-script');
    const transduceTgtScript = document.getElementById('transduce-tgt-script');
    const transduceInput = document.getElementById('transduce-input');
    const transduceBtn = document.getElementById('transduce-btn');
    const transduceOutput = document.getElementById('transduce-output');

    // Sample buttons for LID
    lidSampleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const sample = btn.getAttribute('data-sample');
            if (lidInputText && sample) {
                lidInputText.value = sample;
                if (lidClassifyBtn) lidClassifyBtn.click();
            }
        });
    });

    if (lidClassifyBtn) {
        lidClassifyBtn.addEventListener('click', async () => {
            const text = lidInputText.value.trim();
            if (!text) return;

            lidClassifyBtn.textContent = '🔬 Analyzing...';

            try {
                const response = await fetch('/api/classify_odia_santali', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text })
                });

                if (response.ok) {
                    const data = await response.json();
                    renderLidResult(data);
                }
            } catch (err) {
                console.warn('LID API error, using client heuristic:', err);
                const isSantali = /ଆମ|ଆପେ|ବୟହ|କଵା|ମେନଗ|ସାନାମ|ଏତୁ|ମାଚେତ|ପୁଥି|ଦାଗ|ସେ\?|ଖୋଂ|ବୀର|କନା/.test(text);
                renderLidResult({
                    language: isSantali ? 'sat' : 'ori',
                    language_name: isSantali ? 'Santali (in Odia Script)' : 'Standard Odia',
                    confidence: 0.92,
                    explanation: isSantali ? 'Detected Santali linguistic markers (Mayurbhanj dialect).' : 'Detected Standard Odia morphology.',
                    detected_markers: []
                });
            } finally {
                lidClassifyBtn.innerHTML = '🔬 Detect Language';
            }
        });
    }

    function renderLidResult(data) {
        if (!lidResultBox) return;
        lidResultBox.style.display = 'block';

        const isSat = data.language === 'sat';
        if (lidDetectedLang) {
            lidDetectedLang.innerHTML = isSat
                ? `🎯 Language: <span style="color: #38BDF8;">Santali (sat)</span> <span style="font-size:0.8rem; opacity:0.8;">[Odia Script]</span>`
                : `🎯 Language: <span style="color: #34D399;">Standard Odia (ori)</span>`;
        }

        if (lidConfidencePill) {
            lidConfidencePill.textContent = `Confidence: ${(data.confidence * 100).toFixed(0)}%`;
            lidConfidencePill.style.background = isSat ? 'rgba(56,189,248,0.2)' : 'rgba(52,211,153,0.2)';
            lidConfidencePill.style.color = isSat ? '#38BDF8' : '#34D399';
        }

        if (lidExplanation) {
            lidExplanation.textContent = data.explanation;
        }

        if (lidMarkersList) {
            if (data.detected_markers && data.detected_markers.length > 0) {
                lidMarkersList.innerHTML = `<strong>Matched Lexical Markers:</strong> <code>${data.detected_markers.join('</code>, <code>')}</code>`;
            } else {
                lidMarkersList.innerHTML = '';
            }
        }
    }

    // Multi-Script Transducer
    if (transduceBtn) {
        transduceBtn.addEventListener('click', async () => {
            const text = transduceInput.value.trim();
            if (!text) return;

            const src_script = transduceSrcScript.value;
            const tgt_script = transduceTgtScript.value;

            try {
                const response = await fetch('/api/transduce_script', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text, src_script, tgt_script })
                });

                if (response.ok) {
                    const data = await response.json();
                    const outClass = tgt_script === 'ol_chiki' ? 'ol-chiki-display' : (tgt_script === 'odia' ? 'odia-display' : '');
                    transduceOutput.className = outClass;
                    transduceOutput.innerHTML = data.transduced_text || text;
                }
            } catch (err) {
                console.warn('Transduce error:', err);
            }
        });
    }

    // ------------------------------------------------------------------
    // 5. Vocabulary Bank Table Rendering & Filters
    // ------------------------------------------------------------------
    const VOCAB_DATA = [
        { hin: "नमस्ते", sat_olck: "ᱡᱚᱦᱟᱨ", sat_odia: "ଜୋହାର", eng: "Hello", cat: "Greetings" },
        { hin: "सबको जोहार", sat_olck: "ᱥᱟᱱᱟᱢ ᱠᱚ ᱡᱚᱦᱟᱨ", sat_odia: "ସାନାମ କୋ ଜୋହାର", eng: "Greetings to all", cat: "Greetings" },
        { hin: "धन्यवाद", sat_olck: "ᱥᱟᱨᱦᱟᱣ", sat_odia: "ସାରହାଓ", eng: "Thank you", cat: "Greetings" },
        { hin: "स्वागत है", sat_olck: "ᱥᱟᱹᱜᱩᱱ ᱫᱟᱨᱟᱢ", sat_odia: "ସାଗୁନ ଦାରାମ", eng: "Welcome", cat: "Greetings" },
        { hin: "शिक्षक", sat_olck: "ᱢᱟᱪᱮᱛ", sat_odia: "ମାଚେତ", eng: "Teacher (M)", cat: "School" },
        { hin: "शिक्षिका", sat_olck: "ᱢᱟᱪᱮᱛᱟᱹᱱᱤ", sat_odia: "ମାଚେତନି", eng: "Teacher (F)", cat: "School" },
        { hin: "छात्र / विद्यार्थी", sat_olck: "ᱪᱮᱛᱮᱫᱤᱭᱟᱹ", sat_odia: "ଚେତେଦିୟା", eng: "Student", cat: "School" },
        { hin: "स्कूल / विद्यालय", sat_olck: "ᱤᱛᱩᱱ ᱟᱥᱲᱟ", sat_odia: "ଇତୁନ ଆସଡ଼ା", eng: "School", cat: "School" },
        { hin: "किताब / पुस्तक", sat_olck: "ᱯᱩᱛᱷᱤ", sat_odia: "ପୁଥି", eng: "Book", cat: "School" },
        { hin: "कलम", sat_olck: "ᱠᱚᱞᱚᱢ", sat_odia: "କଲମ", eng: "Pen", cat: "School" },
        { hin: "कापी / पुस्तिका", sat_olck: "ᱚᱞ ᱯᱩᱛᱷᱤ", sat_odia: "ଅଲ ପୁଥି", eng: "Notebook", cat: "School" },
        { hin: "गणित", sat_olck: "ᱞᱮᱠᱷᱟ", sat_odia: "ଲେଖା", eng: "Mathematics", cat: "School" },
        { hin: "पानी", sat_olck: "ᱫᱟᱜ", sat_odia: "ଦାଗ", eng: "Water", cat: "Nature" },
        { hin: "सूरज", sat_olck: "ᱥᱤᱝ ᱪᱟᱸᱫᱚ", sat_odia: "ସିଂ ଚାନ୍ଦୋ", eng: "Sun", cat: "Nature" },
        { hin: "चांद", sat_olck: "ᱧᱤᱸᱫᱟᱹ ᱪᱟᱸᱫᱚ", sat_odia: "ଞିନ୍ଦା ଚାନ୍ଦୋ", eng: "Moon", cat: "Nature" },
        { hin: "पेड़", sat_olck: "ᱫᱟᱨᱮ", sat_odia: "ଦାରେ", eng: "Tree", cat: "Nature" },
        { hin: "फूल", sat_olck: "ᱵᱟᱦᱟ", sat_odia: "ବାହା", eng: "Flower", cat: "Nature" },
        { hin: "फल", sat_olck: "ᱡᱚ", sat_odia: "ଜୋ", eng: "Fruit", cat: "Nature" },
        { hin: "घर", sat_olck: "ᱚᱲᱟᱜ", sat_odia: "ଅଡ଼ାଗ", eng: "Home", cat: "School" },
        { hin: "गांव", sat_olck: "ᱟᱹᱛᱩ", sat_odia: "ଆତୁ / ଏତୁ", eng: "Village", cat: "Nature" },
        { hin: "मां / माता", sat_olck: "ᱟᱭᱳ", sat_odia: "ଆୟୋ", eng: "Mother", cat: "Family" },
        { hin: "पिता / बाप", sat_olck: "ᱵᱟᱵᱟ", sat_odia: "ବାବା", eng: "Father", cat: "Family" },
        { hin: "भाई", sat_olck: "ᱵᱚᱭᱦᱟ", sat_odia: "ବୟହା / ବୟହ", eng: "Brother", cat: "Family" },
        { hin: "बहन", sat_olck: "ᱢᱤᱥᱤ", sat_odia: "ମିସି", eng: "Sister", cat: "Family" },
        { hin: "बच्चा", sat_olck: "ᱜᱤᱫᱽᱨᱟᱹ", sat_odia: "ଗିଦ୍ରା", eng: "Child", cat: "Family" },
        { hin: "दोस्त / मित्र", sat_olck: "ᱜᱟᱛᱮ", sat_odia: "ଗାତେ", eng: "Friend", cat: "Family" },
        { hin: "एक (1)", sat_olck: "ᱢᱤᱫ (᱑)", sat_odia: "ମିଦ (୧)", eng: "One", cat: "Numbers" },
        { hin: "दो (2)", sat_olck: "ᱵᱟᱨ (᱒)", sat_odia: "ବାର (୨)", eng: "Two", cat: "Numbers" },
        { hin: "तीन (3)", sat_olck: "ᱯᱮ (୩)", sat_odia: "ᱯେ (୩)", eng: "Three", cat: "Numbers" },
        { hin: "चार (4)", sat_olck: "ᱯᱩᱱ (᱔)", sat_odia: "ᱯୁନ (୪)", eng: "Four", cat: "Numbers" },
        { hin: "पांच (5)", sat_olck: "ᱢᱚᱬᱮ (᱕)", sat_odia: "ମୋᱬେ (୫)", eng: "Five", cat: "Numbers" },
        { hin: "छह (6)", sat_olck: "ᱛᱩᱨᱩᱭ (᱖)", sat_odia: "ତୁରୁୟ (୬)", eng: "Six", cat: "Numbers" },
        { hin: "सात (7)", sat_olck: "ᱮᱭᱟᱮ (᱗)", sat_odia: "ଏୟାଏ (୭)", eng: "Seven", cat: "Numbers" },
        { hin: "आठ (8)", sat_olck: "ᱤᱨᱟᱹᱞ (᱘)", sat_odia: "ଇରାଲ (୮)", eng: "Eight", cat: "Numbers" },
        { hin: "नौ (9)", sat_olck: "ᱟᱨᱮ (᱙)", sat_odia: "ଆରେ (୯)", eng: "Nine", cat: "Numbers" },
        { hin: "दस (10)", sat_olck: "ᱜᱮᱞ (᱑᱐)", sat_odia: "ଗେଲ (୧୦)", eng: "Ten", cat: "Numbers" }
    ];

    const vocabTableBody = document.getElementById('vocab-table-body');
    const dictSearch = document.getElementById('dict-search');
    const filterBtns = document.querySelectorAll('.filter-btn');

    function renderVocabTable(filterCategory = 'all', searchQuery = '') {
        if (!vocabTableBody) return;
        vocabTableBody.innerHTML = '';

        const query = searchQuery.toLowerCase().trim();

        const filtered = VOCAB_DATA.filter(item => {
            const matchesCat = (filterCategory === 'all' || item.cat === filterCategory);
            const matchesQuery = !query ||
                item.hin.toLowerCase().includes(query) ||
                item.sat_olck.includes(query) ||
                item.sat_odia.includes(query) ||
                item.eng.toLowerCase().includes(query);
            return matchesCat && matchesQuery;
        });

        if (filtered.length === 0) {
            vocabTableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; color: var(--text-muted);">No matching vocabulary entries found</td></tr>`;
            return;
        }

        filtered.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${item.hin}</strong></td>
                <td class="ol-chiki-cell">${item.sat_olck}</td>
                <td class="odia-cell" style="color:#38BDF8;">${item.sat_odia}</td>
                <td>${item.eng}</td>
                <td><span class="badge">${item.cat}</span></td>
                <td><button class="action-icon-btn speak-row-btn" data-text="${item.hin}">🔊</button></td>
            `;
            vocabTableBody.appendChild(tr);
        });

        document.querySelectorAll('.speak-row-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const txt = btn.getAttribute('data-text');
                if ('speechSynthesis' in window && txt) {
                    const utterance = new SpeechSynthesisUtterance(txt);
                    window.speechSynthesis.speak(utterance);
                }
            });
        });
    }

    renderVocabTable();

    if (dictSearch) {
        dictSearch.addEventListener('input', () => {
            const activeFilterBtn = document.querySelector('.filter-btn.active');
            const cat = activeFilterBtn ? activeFilterBtn.getAttribute('data-cat') : 'all';
            renderVocabTable(cat, dictSearch.value);
        });
    }

    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const cat = btn.getAttribute('data-cat');
            renderVocabTable(cat, dictSearch ? dictSearch.value : '');
        });
    });

    // ------------------------------------------------------------------
    // 6. Worksheet Studio Generator
    // ------------------------------------------------------------------
    const generateWsBtn = document.getElementById('generate-ws-btn');
    const wsType = document.getElementById('ws-type');
    const wsTitle = document.getElementById('ws-title');
    const worksheetIframe = document.getElementById('worksheet-iframe');
    const downloadWsBtn = document.getElementById('download-ws-btn');
    const printWsBtn = document.getElementById('print-ws-btn');

    if (generateWsBtn) {
        generateWsBtn.addEventListener('click', async () => {
            const type = wsType.value;
            const title = wsTitle.value;

            generateWsBtn.innerHTML = '⚡ Generating Worksheet...';

            try {
                const response = await fetch('/api/worksheets/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ type, title })
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.html) {
                        worksheetIframe.srcdoc = data.html;
                        if (downloadWsBtn) {
                            downloadWsBtn.classList.remove('disabled');
                            downloadWsBtn.href = 'data:text/html;charset=utf-8,' + encodeURIComponent(data.html);
                        }
                    }
                }
            } catch (e) {
                console.warn('API worksheet generate failed, loading static preview sample:', e);
                const samplePath = type === 'counting' ? 'worksheet_counting.html' : 'worksheet_matching.html';
                worksheetIframe.src = samplePath;
                if (downloadWsBtn) {
                    downloadWsBtn.classList.remove('disabled');
                    downloadWsBtn.href = samplePath;
                }
            } finally {
                generateWsBtn.innerHTML = '<span class="icon">⚡</span> Generate Printable Worksheet';
            }
        });
    }

    if (printWsBtn) {
        printWsBtn.addEventListener('click', () => {
            if (worksheetIframe && worksheetIframe.contentWindow) {
                worksheetIframe.contentWindow.print();
            }
        });
    }

    // ------------------------------------------------------------------
    // 7. Publish & Deploy Snippet Copy Handlers
    // ------------------------------------------------------------------
    document.querySelectorAll('.copy-code-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const code = btn.getAttribute('data-code');
            if (code) {
                navigator.clipboard.writeText(code);
                btn.textContent = '✓ Copied!';
                btn.style.background = '#10B981';
                setTimeout(() => {
                    btn.textContent = '📋 Copy';
                    btn.style.background = '';
                }, 1500);
            }
        });
    });
});
