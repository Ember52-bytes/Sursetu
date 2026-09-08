"""
PALASH Setu - Unified Web Application Backend Server
---------------------------------------------------
Bridges:
  1. Offline Speech Recognition (Vosk ASR Engine from test_mic.py)
  2. Machine Translation Engine (Dictionary & NLLB MT from test_translation.py)
  3. Primary School Worksheet Generator (from worksheets/generator.py)
  4. Web Frontend (index.html, style.css, app.js)
"""

import json
import os
import sys
import time
from flask import Flask, jsonify, request, send_from_directory

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import existing modules
try:
    from test_translation import EDUCATIONAL_DICTIONARY, fallback_translate
except ImportError:
    EDUCATIONAL_DICTIONARY = {}
    fallback_translate = lambda text, s, t: text

try:
    from worksheets.generator import (
        export_worksheet_html,
        generate_counting_worksheet,
        generate_matching_worksheet,
    )
except ImportError:
    generate_counting_worksheet = None
    generate_matching_worksheet = None

# Initialize Flask App
app = Flask(__name__, static_folder=PROJECT_ROOT, static_url_path="")


@app.after_request
def add_cors_headers(response):
    """Ensure all API and asset responses work seamlessly across tunnels & custom domains."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, ngrok-skip-browser-warning, bypass-tunnel-reminder"
    return response


@app.route("/")
def index():
    """Serve main PALASH Setu web interface."""
    return send_from_directory(PROJECT_ROOT, "index.html")


@app.route("/<path:filename>")
def serve_static(filename):
    """Serve CSS, JS, and HTML static assets."""
    return send_from_directory(PROJECT_ROOT, filename)


try:
    from translation_engine import (
        UnsupervisedSantaliTranslator,
        classify_odia_santali,
        transduce_script,
    )
    server_translator = UnsupervisedSantaliTranslator(base_dictionary=EDUCATIONAL_DICTIONARY)
except ImportError:
    server_translator = None
    classify_odia_santali = None
    transduce_script = None

# Initialize Vosk Model on Server for Offline Voice Recognition
vosk_model = None
try:
    import sounddevice as sd
    from vosk import KaldiRecognizer, Model
    from test_mic import find_model_path
    mpath = find_model_path()
    if mpath:
        vosk_model = Model(mpath)
        print(f"[SERVER VOSK] Loaded offline model from: '{mpath}'")
    else:
        print("[SERVER VOSK WARNING] Could not find valid Vosk model directory.")
except Exception as e:
    print(f"[SERVER VOSK WARNING] Could not load Vosk model: {e}")


@app.route("/api/status", methods=["GET"])
def get_status():
    """System health check and loaded engine status."""
    vosk_model_exists = vosk_model is not None

    learned_count = 0
    if server_translator and "hin_Deva" in server_translator.memory:
        learned_count = len(server_translator.memory["hin_Deva"].get("sat_Olck", {}))

    return jsonify({
        "status": "online",
        "vosk_model_loaded": vosk_model_exists,
        "dictionary_languages": list(EDUCATIONAL_DICTIONARY.keys()),
        "learned_words_count": learned_count,
        "engine": "Adaptive & Unsupervised Multi-Layer Engine",
        "version": "1.2.0"
    })


@app.route("/api/asr/record_hardware_mic", methods=["POST"])
def api_record_hardware_mic():
    """Record audio directly from local hardware microphone and transcribe offline with Vosk."""
    if not vosk_model:
        return jsonify({"error": "Vosk speech model not loaded on server"}), 500

    data = request.get_json() or {}
    duration = float(data.get("duration", 3.5))
    target_lang = data.get("target_lang", "sat_Olck")
    samplerate = 16000

    try:
        print(f"[SERVER ASR] Recording hardware mic for {duration} seconds at {samplerate}Hz...")
        recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype="int16")
        sd.wait()

        # Convert numpy int16 array to raw bytes for KaldiRecognizer
        audio_bytes = bytes(recording)
        recognizer = KaldiRecognizer(vosk_model, samplerate)
        recognizer.AcceptWaveform(audio_bytes)
        res = json.loads(recognizer.FinalResult())
        hindi_text = res.get("text", "").strip()

        print(f"[SERVER ASR] Transcribed: '{hindi_text}'")

        # Translate immediately
        translated_text = ""
        confidence = 0.0
        mode = "EMPTY"
        if hindi_text and server_translator:
            trans_res = server_translator.translate(hindi_text, "hin_Deva", target_lang)
            translated_text = trans_res["translated_text"]
            confidence = trans_res["confidence"]
            mode = trans_res["mode"]

        return jsonify({
            "success": True,
            "hindi_text": hindi_text,
            "translated_text": translated_text,
            "confidence": confidence,
            "mode": mode,
            "target_lang": target_lang
        })
    except Exception as err:
        print(f"[SERVER ASR ERROR] {err}")
        return jsonify({"error": f"Microphone recording failed: {err}"}), 500


@app.route("/api/translate", methods=["POST"])
def api_translate():
    """Translation API endpoint supporting Hindi, Santali (Ol Chiki & Odia Script), Mundari, Ho, English."""
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    src = data.get("src", "hin_Deva")
    tgt = data.get("tgt", "sat_Olck")

    if not text:
        return jsonify({"error": "Missing 'text' field"}), 400

    start_time = time.time()
    
    if server_translator and tgt in ["sat_Olck", "sat_Orya"]:
        engine_res = server_translator.translate(text, src, tgt)
        translated_text = engine_res["translated_text"]
        confidence = engine_res["confidence"]
        mode = engine_res["mode"]
        token_breakdown = engine_res.get("token_breakdown", [])
    else:
        translated_text = fallback_translate(text, src, tgt)
        confidence = 1.0
        mode = "EXACT_DICTIONARY"
        token_breakdown = []

    latency_ms = (time.time() - start_time) * 1000

    return jsonify({
        "original_text": text,
        "translated_text": translated_text,
        "source_language": src,
        "target_language": tgt,
        "confidence": confidence,
        "mode": mode,
        "token_breakdown": token_breakdown,
        "latency_ms": round(latency_ms, 2)
    })


@app.route("/api/classify_odia_santali", methods=["POST"])
def api_classify_odia_santali():
    """Classify whether Odia script input is Santali (sat) or Odia (ori)."""
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Missing 'text' parameter"}), 400

    if classify_odia_santali:
        result = classify_odia_santali(text)
        return jsonify({"success": True, **result})

    return jsonify({"error": "Classifier module not available"}), 500


@app.route("/api/transduce_script", methods=["POST"])
def api_transduce_script():
    """Transduce text between Ol Chiki, Odia Script, and Devanagari."""
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    src_script = data.get("src_script", "ol_chiki")
    tgt_script = data.get("tgt_script", "odia")

    if not text:
        return jsonify({"error": "Missing 'text' parameter"}), 400

    if transduce_script:
        output_text = transduce_script(text, src_script, tgt_script)
        return jsonify({
            "success": True,
            "original_text": text,
            "transduced_text": output_text,
            "src_script": src_script,
            "tgt_script": tgt_script
        })

    return jsonify({"error": "Transducer module not available"}), 500


@app.route("/api/learn", methods=["POST"])
def api_learn():
    """Dynamically register a new translation pair into continuous memory."""
    data = request.get_json() or {}
    hindi = data.get("hindi", "").strip()
    santali = data.get("santali", "").strip()
    tgt_lang = data.get("tgt_lang", "sat_Olck")

    if not hindi or not santali:
        return jsonify({"error": "Both 'hindi' and 'santali' fields are required"}), 400

    if server_translator:
        server_translator.learn(hindi, santali, target_lang=tgt_lang)
        return jsonify({
            "success": True,
            "message": f"Successfully learned: '{hindi}' -> '{santali}'",
            "hindi": hindi,
            "santali": santali
        })

    return jsonify({"error": "Translator engine not initialized"}), 500


@app.route("/api/worksheets/generate", methods=["POST"])
def api_generate_worksheet():
    """Worksheet Generator API endpoint."""
    data = request.get_json() or {}
    ws_type = data.get("type", "matching")
    ws_title = data.get("title", "Grade 1 Worksheet")

    if ws_type == "counting" and generate_counting_worksheet:
        ws_data = generate_counting_worksheet(title=ws_title)
    elif generate_matching_worksheet:
        ws_data = generate_matching_worksheet(title=ws_title)
    else:
        return jsonify({"error": "Worksheet generator module not loaded"}), 500

    # Save to temp html file to read html string
    temp_output_path = os.path.join(PROJECT_ROOT, f"temp_worksheet_{ws_type}.html")
    export_worksheet_html(ws_data, temp_output_path)

    html_content = ""
    if os.path.exists(temp_output_path):
        with open(temp_output_path, "r", encoding="utf-8") as f:
            html_content = f.read()

    return jsonify({
        "success": True,
        "title": ws_data.get("title"),
        "type": ws_data.get("type"),
        "html": html_content
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"\n" + "=" * 65)
    print(f"  🚀 PALASH Setu Web Application Server running at:")
    print(f"     http://127.0.0.1:{port}")
    print(f"     http://localhost:{port}")
    print(f"=" * 65 + "\n")
    app.run(host="0.0.0.0", port=port, debug=True)
