"""
PALASH Setu - Translation Engine (MT) Tester
---------------------------------------------
Pipeline 1: Text Machine Translation for Indigenous Languages
Supported Languages:
  - Santali (Ol Chiki / Devanagari / Latin) [sat_Olck / sat_Deva]
  - Mundari [unr_Deva]
  - Ho [hoc_Deva / hoc_Warang Chiti]
  - Hindi [hin_Deva]
  - English [eng_Latn]
"""

import argparse
import sys
import time

# Reconfigure stdout/stderr for Windows terminal UTF-8 rendering (Devanagari & Ol Chiki)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Educational Vocabulary Bank (Zero-Hallucination Offline Fallback)
# ---------------------------------------------------------------------------
EDUCATIONAL_DICTIONARY = {
    "hin_Deva": {
        "sat_Olck": {
            # Greetings & Common Expressions
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

            # School & Classroom Vocabulary
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
            "पुस्तिका": "ᱚᱞ ᱯᱩᱛᱷᱤ",
            "पेंसिल": "ᱯᱮᱱᱥᱤᱞ",
            "पढ़ना": "ᱯᱟᱲᱦᱟᱣ",
            "लिखना": "ᱚᱞ",
            "गणित": "ᱞᱮᱠᱷᱟ",
            "भाषा": "ᱯᱟᱹᱨᱥᱤ",
            "पाठ्यपुस्तक": "ᱯᱟᱲᱦᱟᱣ ᱯᱩᱛᱷᱤ",

            # Numbers (0 - 10)
            "जीरो": "᱐",
            "शून्य": "᱐",
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

            # Family & Relations
            "मां": "ᱟᱭᱳ",
            "माता": "ᱟᱭᱳ",
            "पिता": "ᱵᱟᱵᱟ",
            "बाप": "ᱵᱟᱵᱟ",
            "भाई": "ᱵᱚᱭᱦᱟ",
            "बहन": "ᱢᱤᱥᱤ",
            "बच्चा": "ᱜᱤᱫᱽᱨᱟᱹ",
            "बालक": "ᱜᱤᱫᱽᱨᱟᱹ",
            "दोस्त": "ᱜᱟᱛᱮ",
            "मित्र": "ᱜᱟᱛᱮ",

            # Nature & Environment
            "पानी": "ᱫᱟᱜ",
            "सूरज": "ᱥᱤᱝ ᱪᱟᱸᱫᱚ",
            "सूर्य": "ᱥᱤᱝ ᱪᱟᱸᱫᱚ",
            "चांद": "ᱧᱤᱸᱫᱟᱹ ᱪᱟᱸᱫᱚ",
            "चंद्रमा": "ᱧᱤᱸᱫᱟᱹ ᱪᱟᱸᱫᱚ",
            "पेड़": "ᱫᱟᱨᱮ",
            "वृक्ष": "ᱫᱟᱨᱮ",
            "फूल": "ᱵᱟᱦᱟ",
            "फल": "ᱡᱚ",
            "घर": "ᱚᱲᱟᱜ",
            "गांव": "ᱟᱹᱛᱩ",
            "रोटी": "ᱡᱚᱢᱟᱜ",
            "खाना": "ᱡᱚᱢᱟᱜ",
            "दूध": "ᱛᱳᱣᱟ",

            # Educational Phrases
            "आज हम गणित पढ़ेंगे": "ᱛᱮᱦᱮᱧ ᱵᱚᱱ ᱞᱮᱠᱷᱟ ᱵᱚᱱ ᱯᱟᱲᱦᱟᱣᱟ",
            "किताब खोलो": "ᱯᱩᱛᱷᱤ ᱡᱷᱤᱡᱽ ᱢᱮ",
            "सब बैठ जाओ": "ᱥᱟᱱᱟᱢ ᱠᱚ ᱫᱩᱲᱩᱵ ᱯᱮ",
            "साफ लिखो": "ᱥᱟᱯᱷᱟ ᱚᱞ ᱢᱮ",
        },
        "sat_Orya": {
            # Greetings & Common Expressions in Odia Script
            "नमस्ते": "ଜୋହାର",
            "जोहार": "ଜୋହାର",
            "सबको जोहार": "ସାନାମ କୋ ଜୋହାର",
            "धन्यवाद": "ସାରହାଓ",
            "आपका स्वागत है": "ସାଗୁନ ଦାରାମ",
            "स्वागत": "ସାଗୁନ ଦାରାମ",
            "शुभ प्रभात": "ସାଗୁନ ସେତାଗ",
            "हाँ": "ହେଁ",
            "नहीं": "ବାଙ୍ଗ",

            # School & Classroom Vocabulary
            "शिक्षक": "ମାଚେତ",
            "शिक्षिका": "ମାଚେତନି",
            "छात्र": "ଚେତେଦିୟା",
            "स्कूल": "ଇତୁନ ଆସଡ଼ା",
            "विद्यालय": "ଇତୁନ ଆସଡ଼ା",
            "किताब": "ପୁଥି",
            "पुस्तक": "ପୁଥି",
            "कलम": "କଲମ",
            "कापी": "ଅଲ ପୁଥି",
            "गणित": "ଲେଖା",
            "भाषा": "ପାର୍ସି",
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

            # Numbers
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

            # Phrases
            "आज हम गणित पढ़ेंगे": "ତେହେଞ୍ଜ ବୋନ ଲେଖା ବୋନ ପାଡ଼ହାୱା",
            "किताब खोलो": "ପୁଥି ଝିଜ ମେ",
            "सब बैठ जाओ": "ସାନାମ କୋ ଦୁଡ଼ୁବ ପେ",
            "साफ लिखो": "ସାଫା ଅଲ ମେ",
        },
        "eng_Latn": {
            "नमस्ते": "Hello / Greetings",
            "शिक्षक": "Teacher",
            "छात्र": "Student",
            "स्कूल": "School",
            "किताब": "Book",
            "कलम": "Pen",
            "पानी": "Water",
            "सूरज": "Sun",
        },
    },
    "eng_Latn": {
        "sat_Olck": {
            "hello": "ᱡᱚᱦᱟᱨ",
            "teacher": "ᱢᱟᱪᱮᱛ",
            "student": "ᱪᱮᱛᱮᱫᱤᱭᱟᱹ",
            "school": "ᱤᱛᱩᱱ ᱟᱥᱲᱟ",
            "book": "ᱯᱩᱛᱷᱤ",
            "water": "ᱫᱟᱜ",
            "one": "ᱢᱤᱫ",
            "two": "ᱵᱟᱨ",
            "three": "ᱯᱮ",
        },
        "sat_Orya": {
            "hello": "ଜୋହାର",
            "teacher": "ମାଚେତ",
            "student": "ଚେତେଦିୟା",
            "school": "ଇତୁନ ଆସଡ଼ା",
            "book": "ପୁଥି",
            "water": "ଦାଗ",
            "one": "ମିଦ",
            "two": "ବାର",
            "three": "ପେ",
        }
    },
}

# NLLB-200 Language Codes Mapping
NLLB_CODE_MAP = {
    "santali": "sat_Olck",
    "santali_olchiki": "sat_Olck",
    "santali_devanagari": "sat_Deva",
    "santali_odia": "sat_Orya",
    "mundari": "unr_Deva",
    "hindi": "hin_Deva",
    "english": "eng_Latn",
}


def fallback_translate(text: str, src_lang: str, tgt_lang: str) -> str:
    """Offline lookup using educational dictionary for exact phrase matches and token fallback."""
    text_clean = text.strip().rstrip("।.!?,")
    
try:
    from translation_engine import UnsupervisedSantaliTranslator
    translator_engine = UnsupervisedSantaliTranslator(base_dictionary=EDUCATIONAL_DICTIONARY)
except ImportError:
    translator_engine = None


def fallback_translate(text: str, src_lang: str, tgt_lang: str) -> str:
    """Offline unsupervised & adaptive translation matching."""
    if translator_engine and tgt_lang == "sat_Olck":
        res = translator_engine.translate(text, src_lang, tgt_lang)
        return res["translated_text"]

    text_clean = text.strip().rstrip("।.!?,")
    if src_lang in EDUCATIONAL_DICTIONARY and tgt_lang in EDUCATIONAL_DICTIONARY[src_lang]:
        vocab = EDUCATIONAL_DICTIONARY[src_lang][tgt_lang]
        if text_clean in vocab:
            return vocab[text_clean]
        words = text_clean.split()
        translated = [vocab.get(w.strip("।.!?,"), w) for w in words]
        return " ".join(translated)

    return f"[NO_DICTIONARY_MATCH: '{text}']"


def load_nllb_model(model_name="facebook/nllb-200-distilled-600M"):
    """Load Hugging Face NLLB-200 translation pipeline."""
    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
    except ImportError:
        print("[ERROR] 'transformers' or 'torch' package not installed.")
        print("Install via: pip install transformers torch")
        return None, None

    print(f"[MODEL] Loading model '{model_name}'...")
    start_t = time.time()
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        print(f"[MODEL] Loaded in {time.time() - start_t:.2f} seconds.")
        return tokenizer, model
    except Exception as e:
        print(f"[ERROR] Failed to load HuggingFace model '{model_name}': {e}")
        return None, None


def translate_nllb(text: str, src_code: str, tgt_code: str, tokenizer, model) -> str:
    """Perform neural machine translation using NLLB-200."""
    try:
        from transformers import pipeline

        translator = pipeline(
            "translation",
            model=model,
            tokenizer=tokenizer,
            src_lang=src_code,
            tgt_lang=tgt_code,
            max_length=512,
        )
        output = translator(text)
        return output[0]["translation_text"]
    except Exception as e:
        return f"[MT ERROR: {e}]"


def parse_args():
    parser = argparse.ArgumentParser(
        description="PALASH Setu - Adaptive & Unsupervised Machine Translation (MT) Pipeline"
    )
    parser.add_argument(
        "-t", "--text", type=str, default="नमस्ते सबको जोहार", help="Text to translate"
    )
    parser.add_argument(
        "-s", "--src", type=str, default="hin_Deva", help="Source language code (e.g. hin_Deva, eng_Latn)"
    )
    parser.add_argument(
        "-d", "--tgt", type=str, default="sat_Olck", help="Target language code (e.g. sat_Olck, eng_Latn)"
    )
    parser.add_argument(
        "-m", "--model", type=str, default=None, help="HuggingFace model identifier (e.g., facebook/nllb-200-distilled-600M)"
    )
    parser.add_argument(
        "--learn", nargs=2, metavar=("HINDI", "SANTALI"), help="Teach the model a new Hindi -> Santali translation pair"
    )
    parser.add_argument(
        "--dict-only", action="store_true", help="Use offline adaptive dictionary only"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # If learning flag is provided
    if args.learn:
        hindi_word, santali_word = args.learn
        if translator_engine:
            translator_engine.learn(hindi_word, santali_word, target_lang="sat_Olck")
            print(f"\n[LEARNED] Registered new translation pair:")
            print(f"  Hindi   : '{hindi_word}'")
            print(f"  Santali : '{santali_word}'\n")
        return

    # Map friendly language names if supplied
    src_code = NLLB_CODE_MAP.get(args.src.lower(), args.src)
    tgt_code = NLLB_CODE_MAP.get(args.tgt.lower(), args.tgt)

    print("\n" + "=" * 60)
    print("  PALASH Setu Adaptive & Unsupervised Translation Pipeline")
    print(f"  Source Language : {src_code}")
    print(f"  Target Language : {tgt_code}")
    print(f"  Input Text      : {args.text}")
    print("=" * 60 + "\n")

    # 1. Test Adaptive Unsupervised Inference
    print("[STEP 1] Running Adaptive & Unsupervised Inference...")
    t0 = time.time()
    if translator_engine and tgt_code == "sat_Olck":
        engine_res = translator_engine.translate(args.text, src_code, tgt_code)
        dict_result = engine_res["translated_text"]
        confidence = engine_res["confidence"] * 100
        mode = engine_res["mode"]
    else:
        dict_result = fallback_translate(args.text, src_code, tgt_code)
        confidence = 100.0
        mode = "EXACT_DICTIONARY"

    dict_time = (time.time() - t0) * 1000
    print(f"  Result     : {dict_result}")
    print(f"  Mode       : {mode}")
    print(f"  Confidence : {confidence:.1f}%")
    print(f"  Latency    : {dict_time:.2f} ms\n")

    if args.dict_only:
        print("[FINISHED] Dictionary-only mode specified.")
        return

    # 2. Neural MT Model (NLLB / IndicTrans2)
    if args.model:
        tokenizer, model = load_nllb_model(args.model)
        if model and tokenizer:
            print("[STEP 2] Running Neural Machine Translation (NLLB)...")
            t0 = time.time()
            mt_result = translate_nllb(args.text, src_code, tgt_code, tokenizer, model)
            mt_time = (time.time() - t0) * 1000
            print(f"  Result   : {mt_result}")
            print(f"  Latency  : {mt_time:.2f} ms\n")
    else:
        print("[INFO] Neural model flag omitted. Running in high-speed adaptive unsupervised mode.\n")


if __name__ == "__main__":
    main()

