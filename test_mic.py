import argparse
import json
import os
import queue
import sys

try:
    import sounddevice as sd
except ImportError:
    print("Error: 'sounddevice' package is missing. Install it using: pip install sounddevice")
    sys.exit(1)

try:
    from vosk import KaldiRecognizer, Model
except ImportError:
    print("Error: 'vosk' package is missing. Install it using: pip install vosk")
    sys.exit(1)


# Import translation engine for real-time speech-to-translation
try:
    from translation_engine import UnsupervisedSantaliTranslator
    from test_translation import EDUCATIONAL_DICTIONARY
    translator = UnsupervisedSantaliTranslator(base_dictionary=EDUCATIONAL_DICTIONARY)
except ImportError:
    translator = None


def is_valid_vosk_model(path):
    """Check if directory contains Vosk model assets (am, conf, graph)."""
    if not os.path.isdir(path):
        return False
    return any(os.path.exists(os.path.join(path, item)) for item in ["am", "conf", "graph"])


def find_model_path(custom_path=None):
    """Locate the Vosk model directory automatically, handling nested zip extractions."""
    search_paths = []

    if custom_path:
        search_paths.append(custom_path)

    # Search current directory for matching model folders
    defaults = ["model", "model-hi", "vosk-model-small-hi-0.22", "vosk-model-hi-0.22"]
    for name in os.listdir("."):
        if os.path.isdir(name) and ("vosk" in name.lower() or "model" in name.lower()):
            if name not in search_paths:
                search_paths.append(name)

    for name in defaults:
        if name not in search_paths:
            search_paths.append(name)

    for path in search_paths:
        if not os.path.exists(path) or not os.path.isdir(path):
            continue

        # Check direct path
        if is_valid_vosk_model(path):
            return path

        # Check for nested subfolder from zip extraction (e.g. folder/folder/)
        try:
            for sub in os.listdir(path):
                subpath = os.path.join(path, sub)
                if is_valid_vosk_model(subpath):
                    return subpath
        except OSError:
            pass

    return None


def list_audio_devices():
    """Print available audio input devices."""
    print("\n--- Available Input Devices ---")
    devices = sd.query_devices()
    for idx, dev in enumerate(devices):
        if dev["max_input_channels"] > 0:
            default_mark = " (Default)" if idx == sd.default.device[0] else ""
            print(f"ID {idx}: {dev['name']}{default_mark} - {int(dev['default_samplerate'])} Hz")
    print("-------------------------------\n")


def parse_args():
    parser = argparse.ArgumentParser(
        description="PALASH Setu - Real-Time Offline Speech-to-Text (ASR) & Translation using Vosk"
    )
    parser.add_argument(
        "-m", "--model", type=str, default=None, help="Path to Vosk Hindi model directory"
    )
    parser.add_argument(
        "-d", "--device", type=int, default=None, help="Audio input device ID (run --list-devices to view)"
    )
    parser.add_argument(
        "-r", "--samplerate", type=int, default=None, help="Target sample rate in Hz (e.g. 16000)"
    )
    parser.add_argument(
        "-t", "--target-lang", type=str, default="sat_Olck", help="Target translation language (default: sat_Olck)"
    )
    parser.add_argument(
        "-l", "--list-devices", action="store_true", help="List all input audio devices and exit"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.list_devices:
        list_audio_devices()
        return

    # 1. Resolve Model Path
    model_path = find_model_path(args.model)
    if not model_path:
        print("[ERROR] Could not find a valid Vosk model directory!")
        print("\nPlease download a Hindi model from Alphacephei Vosk models:")
        print("  1. Download: https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip")
        print("  2. Extract it into this directory as 'model' or 'vosk-model-small-hi-0.22'")
        print("  3. Or specify path: python test_mic.py -m /path/to/model\n")
        sys.exit(1)

    print(f"[MODEL] Loading Vosk model from: '{model_path}'...")
    try:
        model = Model(model_path)
    except Exception as e:
        print(f"[ERROR] Failed to load model from '{model_path}': {e}")
        sys.exit(1)

    # 2. Configure Audio Device & Sample Rate (Vosk model performs best at 16000 Hz)
    device = args.device if args.device is not None else sd.default.device[0]
    device_info = sd.query_devices(device, "input")
    samplerate = args.samplerate or 16000

    print(f"[AUDIO] Device: '{device_info['name']}' (ID: {device})")
    print(f"[AUDIO] Sample Rate: {samplerate} Hz (Optimized for Vosk)")
    print(f"[TARGET LANG] {args.target_lang}")

    recognizer = KaldiRecognizer(model, samplerate)
    audio_queue = queue.Queue()

    def audio_callback(indata, frames, time, status):
        if status:
            print(f"[AUDIO WARNING] {status}", file=sys.stderr)
        audio_queue.put(bytes(indata))

    print("\n" + "=" * 65)
    print("  🎙️ PALASH Setu Live Voice Input -> Santali (Ol Chiki) Translator")
    print("  Speak into your microphone in Hindi (e.g. 'नमस्ते शिक्षक').")
    print("  Press Ctrl+C to stop.")
    print("=" * 65 + "\n")

    last_partial = ""

    try:
        with sd.RawInputStream(
            samplerate=samplerate,
            blocksize=4000,
            device=device,
            dtype="int16",
            channels=1,
            callback=audio_callback,
        ):
            while True:
                data = audio_queue.get()
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").strip()
                    if text:
                        # Clear partial line and print recognized & translated output
                        sys.stdout.write("\r" + " " * 110 + "\r")
                        print(f"🎙️ [VOICE HINDI]    : {text}")
                        if translator:
                            trans_res = translator.translate(text, "hin_Deva", args.target_lang)
                            print(f"🌐 [INSTANT SANTALI] : {trans_res['translated_text']}  (Confidence: {int(trans_res['confidence']*100)}% | {trans_res['mode']})")
                        print("-" * 65)
                        sys.stdout.flush()
                        last_partial = ""
                else:
                    partial_res = json.loads(recognizer.PartialResult())
                    partial_text = partial_res.get("partial", "").strip()
                    if partial_text and partial_text != last_partial:
                        last_partial = partial_text
                        live_trans_text = ""
                        if translator:
                            live_trans = translator.translate(partial_text, "hin_Deva", args.target_lang)
                            live_trans_text = f" ➔ 🌐 {live_trans['translated_text']}"
                        sys.stdout.write(f"\r⏳ [LIVE STREAM] {partial_text}{live_trans_text}")
                        sys.stdout.flush()

    except KeyboardInterrupt:
        sys.stdout.write("\r" + " " * 110 + "\r")
        final_res = json.loads(recognizer.FinalResult())
        final_text = final_res.get("text", "").strip()
        if final_text:
            print(f"🎙️ [FINAL HINDI]    : {final_text}")
            if translator:
                trans_res = translator.translate(final_text, "hin_Deva", args.target_lang)
                print(f"🌐 [FINAL SANTALI]  : {trans_res['translated_text']}")
        print("\n[STOPPED] Real-time voice session ended cleanly.")
    except Exception as error:
        print(f"\n[ERROR] Audio processing failed: {error}")


if __name__ == "__main__":
    main()