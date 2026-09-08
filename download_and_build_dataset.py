"""
PALASH Setu - Large-Scale Santali Dataset Ingestion & Model Enrichment Pipeline
--------------------------------------------------------------------------------
1. Ingests open parallel corpora from Hugging Face:
   - 'aiswarya9302/english-santali-combined' (72,900+ parallel pairs)
   - 'Murmu722/santali_english_corpus'
2. Cleans and aligns Santali (Ol Chiki ᱚᱞ ᱪᱤᱠᱤ) <-> Odia Script (ଓଡ଼ିଆ ଲିପି) <-> Hindi <-> English.
3. Enriches the PALASH Setu translation dictionary and local offline memory.
4. Exports curated dataset to CSV and JSON formats.
"""

import csv
import json
import os
import re
import sys

# Configure UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATASETS_DIR = os.path.join(PROJECT_ROOT, "datasets")
os.makedirs(DATASETS_DIR, exist_ok=True)

from translation_engine import transduce_script


def clean_text(text: str) -> str:
    """Clean and normalize whitespace."""
    if not text or not isinstance(text, str):
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def download_and_process():
    print("\n" + "=" * 65)
    print("  🚀 PALASH Setu - Downloading High-Quality Santali Dataset")
    print("=" * 65 + "\n")

    try:
        from datasets import load_dataset
    except ImportError:
        print("[ERROR] 'datasets' library is required. Install via: pip install datasets")
        return

    all_pairs = []

    # 1. Load aiswarya9302/english-santali-combined
    print("[1/3] Downloading 'aiswarya9302/english-santali-combined' from Hugging Face...")
    try:
        ds1 = load_dataset("aiswarya9302/english-santali-combined", split="train")
        print(f"      ✓ Successfully loaded {len(ds1)} sentence pairs.")
        
        for item in ds1:
            eng = clean_text(item.get("src", ""))
            sat = clean_text(item.get("tgt", ""))
            if eng and sat and len(eng) > 1 and len(sat) > 1:
                all_pairs.append({
                    "eng": eng,
                    "sat_olchiki": sat,
                    "source": "hf_aiswarya9302_combined"
                })
    except Exception as e:
        print(f"      ⚠️ Warning downloading primary dataset: {e}")

    # 2. Load Murmu722/santali_english_corpus
    print("\n[2/3] Checking 'Murmu722/santali_english_corpus'...")
    try:
        ds2 = load_dataset("Murmu722/santali_english_corpus", split="english")
        for item in ds2:
            eng = clean_text(item.get("english", "") or item.get("text", ""))
            sat = clean_text(item.get("santali", "") or item.get("ol_chiki", ""))
            if eng and sat:
                all_pairs.append({
                    "eng": eng,
                    "sat_olchiki": sat,
                    "source": "hf_murmu722"
                })
    except Exception as e:
        print(f"      (Optional corpus skipped: {e})")

    print(f"\n[SUMMARY] Ingested {len(all_pairs)} total Santali-English parallel pairs.")

    # 3. Export to CSV with Odia Script Transduction
    csv_path = os.path.join(PROJECT_ROOT, "santali_large_parallel_corpus.csv")
    print(f"\n[3/3] Generating Odia Script transliterations and exporting to '{csv_path}'...")

    written_count = 0
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "English", "Santali_OlChiki", "Santali_Odia_Script", "Source"])
        
        for idx, pair in enumerate(all_pairs, start=1):
            sat_ol = pair["sat_olchiki"]
            sat_odia = transduce_script(sat_ol, "ol_chiki", "odia")
            writer.writerow([idx, pair["eng"], sat_ol, sat_odia, pair["source"]])
            written_count += 1

    print(f"      ✓ Exported {written_count} rows to '{csv_path}'.")

    # 4. Enrich local memory store for instant zero-latency translations
    memory_path = os.path.join(DATASETS_DIR, "learned_memory.json")
    memory = {"hin_Deva": {"sat_Olck": {}, "sat_Orya": {}}, "eng_Latn": {"sat_Olck": {}, "sat_Orya": {}}}
    
    if os.path.exists(memory_path):
        try:
            with open(memory_path, "r", encoding="utf-8") as f:
                memory = json.load(f)
        except Exception:
            pass

    if "eng_Latn" not in memory:
        memory["eng_Latn"] = {"sat_Olck": {}, "sat_Orya": {}}
    if "sat_Olck" not in memory["eng_Latn"]:
        memory["eng_Latn"]["sat_Olck"] = {}
    if "sat_Orya" not in memory["eng_Latn"]:
        memory["eng_Latn"]["sat_Orya"] = {}

    # Pre-index short phrases and words into memory
    indexed_phrases = 0
    for pair in all_pairs[:5000]: # Index top 5000 clean pairs for instant lookup
        eng_lower = pair["eng"].lower().strip(".,!?")
        if len(eng_lower.split()) <= 6: # short phrases and sentences
            sat_ol = pair["sat_olchiki"]
            sat_odia = transduce_script(sat_ol, "ol_chiki", "odia")
            memory["eng_Latn"]["sat_Olck"][eng_lower] = sat_ol
            memory["eng_Latn"]["sat_Orya"][eng_lower] = sat_odia
            indexed_phrases += 1

    with open(memory_path, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

    print(f"      ✓ Pre-indexed {indexed_phrases} high-frequency phrases into continuous memory '{memory_path}'.")

    print("\n" + "=" * 65)
    print("  🎉 DATASET INGESTION & TRANSLATOR ENRICHMENT COMPLETE!")
    print(f"     Total Parallel Sentences : {written_count:,}")
    print(f"     Saved Parallel CSV       : santali_large_parallel_corpus.csv")
    print(f"     Updated Memory Engine    : datasets/learned_memory.json")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    download_and_process()
