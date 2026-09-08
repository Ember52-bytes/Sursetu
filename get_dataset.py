import csv
import os
import pandas as pd
from datasets import load_dataset
from translation_engine import transduce_script

print("\n" + "=" * 60)
print("  Downloading & Updating Large-Scale Santali Dataset...")
print("=" * 60 + "\n")

# 1. Download the English-Santali Parallel Corpus from Hugging Face
print("[1/2] Fetching 72,900+ sentences from 'aiswarya9302/english-santali-combined'...")
dataset = load_dataset("aiswarya9302/english-santali-combined", split="train")

# 2. Convert to DataFrame and add Odia script transduction
print("[2/2] Generating multi-script parallel dataset (English, Ol Chiki, Odia Script)...")
df = dataset.to_pandas()
df.rename(columns={"src": "English", "tgt": "Santali_OlChiki"}, inplace=True)
df["Santali_Odia_Script"] = df["Santali_OlChiki"].apply(lambda text: transduce_script(str(text), "ol_chiki", "odia"))

# 3. Save as CSV
output_csv = "santali_dataset.csv"
df.to_csv(output_csv, index=False, encoding="utf-8-sig")

print(f"\n[SUCCESS] Saved {len(df):,} parallel Santali pairs to '{output_csv}'!")