"""
PALASH Setu - Santali Dataset Loader & Utility
------------------------------------------------
Provides easy access to local Santali (Ol Chiki ᱚᱞ ᱪᱤᱠᱤ / Devanagari) datasets
and information on major open-source Santali language benchmarks.
"""

import json
import os
import sys

# Reconfigure stdout/stderr for Windows terminal UTF-8 rendering
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

DATASET_PATH = os.path.join(os.path.dirname(__file__), "santali_dictionary.json")


def load_santali_dataset():
    """Load local Santali education dataset JSON."""
    if os.path.exists(DATASET_PATH):
        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def export_to_csv(output_csv_path="santali_vocab.csv"):
    """Export vocabulary dataset to CSV format."""
    data = load_santali_dataset()
    vocab = data.get("vocabulary", [])
    if not vocab:
        print("[ERROR] No vocabulary dataset found.")
        return

    import csv
    with open(output_csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Hindi", "Santali_OlChiki", "Santali_Devanagari", "English", "Phonetic", "Category"])
        for item in vocab:
            writer.writerow([
                item.get("id"),
                item.get("hin"),
                item.get("sat_olchiki"),
                item.get("sat_devanagari"),
                item.get("eng"),
                item.get("phonetic"),
                item.get("category")
            ])
    print(f"[EXPORT] Santali vocabulary dataset exported to CSV: '{output_csv_path}'")


def print_dataset_summary():
    """Print dataset statistics and major open benchmark pointers."""
    data = load_santali_dataset()
    vocab = data.get("vocabulary", [])
    sentences = data.get("parallel_sentences", [])
    numerals = data.get("numerals", [])

    large_corpus_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "santali_large_parallel_corpus.csv")
    large_count = 0
    if os.path.exists(large_corpus_path):
        with open(large_corpus_path, "r", encoding="utf-8") as f:
            large_count = sum(1 for _ in f) - 1

    print("\n============================================================")
    print("  PALASH Setu - Santali ( Ol Chiki ᱚᱞ ᱪᱤᱠᱤ / Odia Script ଓଡ଼ିଆ ) Dataset Summary")
    print("============================================================\n")
    print(f"  • Vocabulary Bank      : {len(vocab)} verified primary education entries")
    print(f"  • Ol Chiki & Odia Digits: {len(numerals)} numerals (᱐-᱙ / ୦-୯)")
    print(f"  • Parallel Sentences   : {len(sentences)} curated curriculum pairs")
    print(f"  • Large Parallel Corpus: {large_count:,} pairs in 'santali_large_parallel_corpus.csv'")
    print(f"  • Primary Dataset Path : '{DATASET_PATH}'\n")

    print("------------------------------------------------------------")
    print(" Major Open-Source Santali Datasets for AI & NLP:")
    print("------------------------------------------------------------")
    print(" 1. AISWARYA Combined Corpus: 'aiswarya9302/english-santali-combined' (72,900+ pairs)")
    print(" 2. FLORES-200 Benchmark (Meta AI) - 'sat_Olck' & 'sat_Deva'")
    print(" 3. BPCC & IndicTrans2 (AI4Bharat) - Hindi-Santali & English-Santali")
    print(" 4. IndicCorp v2 (AI4Bharat) - Monolingual Santali text corpus")
    print("============================================================\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--csv":
        export_to_csv()
    else:
        print_dataset_summary()
