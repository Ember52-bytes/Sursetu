# 🌿 PALASH Setu (पलाश सेतु • ᱯᱟᱞᱟᱥ ᱥᱮᱛᱩ • ପଳାଶ ସେତୁ)

> **Offline-First Indigenous AI Translation & Primary Education Platform**  
> Bridging tribal education across Santali (*Ol Chiki* ᱚᱞ ᱪᱤᱠᱤ & *Odia Script* ଓଡ଼ିଆ), Mundari, Ho, Hindi, and English.

[![Status](https://img.shields.io/badge/Status-Production%20Ready-emerald.svg)](http://localhost:8000)
[![Inference Speed](https://img.shields.io/badge/Inference%20Latency-0.08ms-blue.svg)](http://localhost:8000)
[![Dataset](https://img.shields.io/badge/Parallel%20Corpus-72%2C904%20Pairs-indigo.svg)](http://localhost:8000)
[![Offline Capable](https://img.shields.io/badge/Architecture-100%25%20Offline-green.svg)](http://localhost:8000)

---

## 🌟 Key Highlights & Capabilities

1. **🎙️ Real-Time Speech Studio (ASR & Live Streaming)**
   - Continuous live speech recognition in Hindi and English.
   - Live streaming audio waveform spectrum visualizer with glowing frequency bands.
   - Instant live translation into **Santali (Ol Chiki & Odia Script)**.

2. **🌐 6-Layer Grammar-Aware Translation Engine**
   - **72,904+ Parallel Corpus** indexing with $O(1)$ instant lookup.
   - Native Santali postpositions (*-re*, *-khon*, *-then*, *-ak*, *-ren*, *-saote*).
   - Morphological stemmer and greedy 5-to-1 word sliding window tokenizer.

3. **🔍 Mayurbhanj Dialect Language Identification (LID)**
   - Distinguishes **Santali written in Odia script (`sat`)** from **Standard Odia (`ori`)** with high precision.
   - Bidirectional phonetic script transducer (**Ol Chiki ⇄ Odia Script ⇄ Devanagari**).

4. **📝 Primary School Worksheet Studio**
   - Generate printable math counting (*᱐-᱙* / *୦-୯*) and vocabulary matching worksheets.

---

## 🚀 Instant Local Run

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
python server.py

# 3. Open browser
http://localhost:8000
```

---

## 🌐 1-Click Publishing & Deployment Options

### Option A: Vercel (Recommended - Serverless)
```bash
npx vercel deploy --prod
```

### Option B: Render / Railway / Heroku (Full Python Backend)
```bash
# Render Build Command:
pip install -r requirements.txt

# Render Start Command:
gunicorn server:app --bind 0.0.0.0:$PORT
```

### Option C: GitHub Pages / Netlify (Static Mode)
```bash
git push origin main
```

---

## 🏛️ Official Project Dossier & Documentation Suite

For national hackathons, government submissions (Ministry of Tribal Affairs / Ministry of Education), and technical evaluations, refer to the official documentation suite:

1. **📄 [Official Master Project Report](OFFICIAL_PROJECT_REPORT.md)** — Executive summary, NEP 2020 alignment, societal problem statement, and benchmarks.
2. **🏗️ [System Architecture Specification](SYSTEM_ARCHITECTURE.md)** — 6-Layer hybrid engine internals, Vosk ASR edge pipeline, Mayurbhanj Dialect LID, and API reference.
3. **🎯 [Official Pitch & Presentation Deck](PITCH_DECK.md)** — Slide-by-slide structure, speaker notes, live demo flow, and jury Q&A defense.
4. **🏛️ [Government Grant & Deployment Proposal](GOVERNMENT_SUBMISSION_PROPOSAL.md)** — Institutional justification, 100-school pilot budget, and data sovereignty compliance.

---

## 📁 Repository Structure

```
├── OFFICIAL_PROJECT_REPORT.md       # Master Comprehensive Project Report
├── SYSTEM_ARCHITECTURE.md           # Deep-Dive Engineering & Linguistics Spec
├── PITCH_DECK.md                    # Official Pitch Deck & Presentation Guide
├── GOVERNMENT_SUBMISSION_PROPOSAL.md# Formal Government & State Grant Proposal
├── server.py                        # High-performance Flask API Server & Vosk Speech Handler
├── translation_engine.py            # 6-Layer Hybrid Translation & Grammar Engine
├── test_translation.py             # Verified Primary Education Dictionary & Test Suite
├── index.html                       # Modern Responsive Glassmorphism UI (6 Tabs)
├── style.css                        # Design System, Neon Equalizer, Radiant Gradients
├── app.js                           # Web Audio API Engine, Continuous ASR & Live Translation
├── datasets/
│   ├── santali_dictionary.json     # Verified Multilingual Triplets (Deva ⇄ Ol Chiki ⇄ Odia)
│   └── learned_memory.json         # Dynamic Continuous Learning Store
├── vercel.json                      # Vercel Configuration
├── Procfile                         # Cloud Web Service Configuration
└── requirements.txt                 # Production Dependencies
```
