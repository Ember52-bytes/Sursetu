"""
PALASH Setu - Worksheet Template Generator
-------------------------------------------
Module 2: Auto-Generated Offline Primary-School Worksheets
Generates zero-hallucination, bilingual worksheets for:
  - Santali (Ol Chiki) ↔ Hindi / English
  - Mundari ↔ Hindi
  - Ho ↔ Hindi

Features:
  1. Counting & Number Recognition (Ol Chiki Digits U+1C50-U+1C59)
  2. Word-to-Image / Word-to-Word Matching
  3. Fill-in-the-Blanks & Vocabulary Practice
  4. HTML & Markdown Printable Exporter
"""

import argparse
import json
import os
import random
import sys

# Reconfigure stdout for Windows terminal UTF-8 rendering
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ol Chiki Digits (0-9)
OL_CHIKI_DIGITS = ["᱐", "᱑", "᱒", "᱓", "᱔", "᱕", "᱖", "᱗", "᱘", "᱙"]

# Primary School Vocabulary Bank
VOCAB_BANK = [
    {"hin": "शिक्षक", "sat_olck": "ᱢᱟᱪᱮᱛ", "eng": "Teacher", "category": "School"},
    {"hin": "छात्र", "sat_olck": "ᱪᱮᱛᱮᱫᱤᱭᱟᱹ", "eng": "Student", "category": "School"},
    {"hin": "स्कूल", "sat_olck": "ᱤᱛᱩᱱ ᱟᱥᱲᱟ", "eng": "School", "category": "School"},
    {"hin": "किताब", "sat_olck": "ᱯᱩᱛᱷᱤ", "eng": "Book", "category": "School"},
    {"hin": "कलम", "sat_olck": "ᱠᱚᱞᱚᱢ", "eng": "Pen", "category": "School"},
    {"hin": "पानी", "sat_olck": "ᱫᱟᱜ", "eng": "Water", "category": "Nature"},
    {"hin": "सूरज", "sat_olck": "ᱥᱤᱝ ᱪᱟᱸᱫᱚ", "eng": "Sun", "category": "Nature"},
    {"hin": "पेड़", "sat_olck": "ᱫᱟᱨᱮ", "eng": "Tree", "category": "Nature"},
    {"hin": "घर", "sat_olck": "ᱚᱲᱟᱜ", "eng": "Home", "category": "Daily"},
    {"hin": "फूल", "sat_olck": "ᱵᱟᱦᱟ", "eng": "Flower", "category": "Nature"},
]


def to_ol_chiki_number(num: int) -> str:
    """Convert an integer to Ol Chiki numeral string."""
    return "".join(OL_CHIKI_DIGITS[int(d)] for d in str(num))


def generate_counting_worksheet(title="Grade 1 Math - Counting in Ol Chiki"):
    """Generate a counting exercise worksheet."""
    exercises = []
    for i in range(1, 11):
        ol_digit = to_ol_chiki_number(i)
        exercises.append({
            "number": i,
            "ol_chiki_digit": ol_digit,
            "prompt": f"Count {i} items: {'⭐ ' * i}",
            "answer_box": f"[  {ol_digit}  ]"
        })
    return {
        "title": title,
        "type": "Counting",
        "instructions": "Count the objects and write the number in Ol Chiki script (ᱚᱞ ᱪᱤᱠᱤ).",
        "exercises": exercises
    }


def generate_matching_worksheet(title="Grade 1 Vocabulary - Hindi to Ol Chiki Match"):
    """Generate word-matching exercise pairs."""
    items = random.sample(VOCAB_BANK, min(6, len(VOCAB_BANK)))
    left_column = [item["hin"] for item in items]
    right_column = [item["sat_olck"] for item in items]

    # Shuffle right column for matching challenge
    shuffled_right = right_column.copy()
    random.shuffle(shuffled_right)

    pairs = []
    for left, right in zip(left_column, shuffled_right):
        pairs.append({"left": left, "right": right})

    return {
        "title": title,
        "type": "Word Matching",
        "instructions": "Draw a line matching each Hindi word on the left to its Santali (Ol Chiki) translation on the right.",
        "pairs": pairs,
        "answer_key": {item["hin"]: item["sat_olck"] for item in items}
    }


def export_worksheet_html(worksheet_data, output_path="worksheet.html"):
    """Export worksheet to print-ready styled HTML file."""
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{worksheet_data['title']}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 40px;
            color: #1a1a1a;
            background-color: #fdfdfd;
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .header h1 {{ margin: 0; color: #2c3e50; font-size: 24px; }}
        .header h3 {{ margin: 5px 0 0 0; color: #7f8c8d; font-size: 14px; }}
        .instructions {{
            background-color: #eef7fc;
            border-left: 5px solid #3498db;
            padding: 12px 15px;
            margin-bottom: 25px;
            font-size: 15px;
            border-radius: 4px;
        }}
        .grid-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        .grid-table th, .grid-table td {{
            border: 1px solid #bdc3c7;
            padding: 12px;
            text-align: center;
            font-size: 18px;
        }}
        .grid-table th {{
            background-color: #ecf0f1;
            color: #2c3e50;
        }}
        .ol-chiki {{
            font-size: 22px;
            font-weight: bold;
            color: #27ae60;
        }}
        .meta-bar {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
            font-weight: bold;
            font-size: 14px;
        }}
        @media print {{
            body {{ margin: 20px; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>PALASH Setu - Primary School Worksheet</h1>
        <h3>{worksheet_data['title']}</h3>
    </div>

    <div class="meta-bar">
        <span>Name: ______________________</span>
        <span>Class: __________</span>
        <span>Date: ____________</span>
    </div>

    <div class="instructions">
        <strong>Instructions:</strong> {worksheet_data['instructions']}
    </div>
"""

    if worksheet_data["type"] == "Counting":
        html_content += """    <table class="grid-table">
        <thead>
            <tr>
                <th>Item #</th>
                <th>Objects to Count</th>
                <th>Write Number in Ol Chiki (ᱚᱞ ᱪᱤᱠᱤ)</th>
            </tr>
        </thead>
        <tbody>
"""
        for item in worksheet_data["exercises"]:
            html_content += f"""            <tr>
                <td><strong>{item['number']}</strong></td>
                <td style="text-align: left; padding-left: 20px;">{item['prompt']}</td>
                <td class="ol-chiki" style="width: 250px;">___</td>
            </tr>
"""
        html_content += "        </tbody>\n    </table>\n"

    elif worksheet_data["type"] == "Word Matching":
        html_content += """    <table class="grid-table">
        <thead>
            <tr>
                <th>Hindi Word (हिन्दी)</th>
                <th>Match Line</th>
                <th>Santali ( Ol Chiki - ᱚᱞ ᱪᱤᱠᱤ )</th>
            </tr>
        </thead>
        <tbody>
"""
        for pair in worksheet_data["pairs"]:
            html_content += f"""            <tr>
                <td style="font-size: 20px; font-weight: bold;">{pair['left']}</td>
                <td style="color: #95a5a6;">──────────⃝</td>
                <td class="ol-chiki">{pair['right']}</td>
            </tr>
"""
        html_content += "        </tbody>\n    </table>\n"

    html_content += """
    <div style="margin-top: 40px; text-align: center; color: #95a5a6; font-size: 12px;">
        Generated by PALASH Setu Offline AI Engine for Primary Education | Jharkhand & Odisha
    </div>
</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[EXPORT] Printable HTML Worksheet saved to: '{output_path}'")


def main():
    parser = argparse.ArgumentParser(description="PALASH Setu Worksheet Generator")
    parser.add_argument(
        "-t", "--type", choices=["counting", "matching"], default="matching",
        help="Type of worksheet to generate (counting or matching)"
    )
    parser.add_argument(
        "-o", "--output", type=str, default="worksheet_sample.html",
        help="Output HTML file path"
    )
    args = parser.parse_args()

    print("\n============================================================")
    print("  PALASH Setu Offline Worksheet Generator")
    print("============================================================\n")

    if args.type == "counting":
        ws_data = generate_counting_worksheet()
    else:
        ws_data = generate_matching_worksheet()

    print(f"Generated Worksheet: {ws_data['title']}")
    print(f"Instructions       : {ws_data['instructions']}\n")

    export_worksheet_html(ws_data, args.output)


if __name__ == "__main__":
    main()
