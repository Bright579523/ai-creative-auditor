---
title: Ai Creative Auditor
emoji: 🚀
colorFrom: yellow
colorTo: yellow
sdk: docker
pinned: false
license: mit
---

# AI Creative Auditor

An intelligent ad creative evaluation system that combines local Computer Vision pipelines with structured Large Language Model (LLM) scoring and DuckDB analytics. Built to help marketing teams and data analysts make data-driven visual asset decisions.

**[Live Demo on Hugging Face Spaces](https://huggingface.co/spaces/Bright87/ai-creative-auditor)**  
*Note: All original ad images are processed locally on the host machine to respect GDPR and user privacy guidelines.*

---

## The Journey: From V1 to V2

This project began with a straightforward concept in **Version 1 (V1)**: helping marketers quickly screen ad creatives. In V1, the application allowed users to upload a single image to extract text, detect human presence, and get a basic, general design score with brief feedback spanning four broad categories.

However, real-world testing revealed key limitations: the scoring lacked granular business context, color extraction didn't align with visual psychology, there was no built-in accessibility compliance checking, and users had no way to compare creatives side-by-side (A/B testing) or view a visual history of previously analyzed assets.

To address these needs, we built **Version 2 (V2)**. While keeping the core concept of a **"Hybrid Local CV + Cloud LLM Auditor"**, we upgraded the architecture and introduced several professional features:

1. **Structured & Granular Scoring**: Separated the evaluation into distinct Design and Business scores. It now provides a detailed breakdown across four dimensions: Visual Hierarchy, Color Psychology, Message Clarity, and Audience Fit, validated reliably using Pydantic schemas.
2. **Color Psychology Analytics**: Instead of just listing basic color names like V1, V2 uses K-Means Clustering to extract precise HEX values, calculate visual coverage %, and map them to advertising psychology tags (e.g., trust, energy, warmth, calmness).
3. **Accessibility Guardrails**: Integrated a WCAG contrast ratio heuristic. By sampling the text and surrounding background colors within OCR bounding boxes, it alerts designers if copy is hard to read.
4. **Interactive A/B Creative Comparison**: Designed a dedicated comparison view allowing users to upload two creatives side-by-side, calculate delta scores, and automatically declare a winner based on unified performance.
5. **Visual-First Analytics Dashboard**: Replaced the dry spreadsheets of V1 with a rich historical gallery powered by DuckDB. Marketing teams can now view all previously evaluated assets, filter by segments, inspect color psychology distributions, and export data as CSV.

### Performance & Stability Upgrades
* **Instant App Startup**: In V1, model weights for EasyOCR and YOLOv8 had to download on the fly, creating long deployment timeouts. In V2, we optimized the `Dockerfile` to pre-download all required models (both English and Thai packs) during the Docker build stage. The app now launches instantly.
* **Anti-Flicker & Stable UI**: Added transition styles and layout min-height parameters in `assets/custom.css` to prevent layout jumps (screen jittering) when switching tabs or waiting for analysis.
* **Streamlined Deployment with Git LFS**: Set up proper Git LFS tracking for the sample image dataset and DuckDB files. We also established an orphan-branch deployment pipeline to ensure clean pushes to Hugging Face Spaces.

---

## System Architecture

```
[User Upload] ──> [Local CV Processing] ──> [Metadata & OCR Text] ──> [LLM Evaluation] ──> [Database & Dashboard]
                         │                                                   │                         │
                   - YOLOv8 (People Count)                             - Groq API                    - DuckDB
                   - EasyOCR (Text Detection)                         (Llama 3.3 70B)                - Streamlit
                   - K-Means (Colors & HEX)                           - Pydantic Validation          - Plotly Charts
                   - WCAG Heuristic (Contrast)
```

*Note: Raw images never leave the host server. Only extracted non-PII metadata, color names, and OCR text are sent to the LLM API, ensuring compliance with data privacy standards.*

---

## Repository Structure

```
├── app.py                 # Streamlit UI application (Audit, A/B Comparison, Analytics)
├── ui_helpers.py          # Visual chart renderers, score gauges, and UI helpers
├── vision_ops.py          # Local computer vision pipeline (YOLO, OCR, K-Means, WCAG)
├── run_pipeline.py        # Groq LLM client runner and offline batch processing pipeline
├── schemas.py             # Pydantic models enforcing structured JSON outputs
├── database_ops.py        # Database connectors for writing and reading with DuckDB
├── init_db.py             # Script to initialize or upgrade the database schema
├── migrate_db_v2.py       # Helper script to migrate existing databases to V2
├── assets/custom.css      # Styling rules containing the layout anti-flicker fixes
├── docs/CASE_STUDY.md     # Business case study, GDPR details, and project limitations
├── tests/                 # Unit tests (pytest suite)
├── notebooks/             # Jupyter notebooks for EDA and model evaluation
├── requirements.txt       # Python dependencies
└── Dockerfile             # Multi-stage Docker configuration optimized for fast startup
```

---

## Core Tech Stack

* **Frontend & Charts:** Streamlit 1.40, Plotly, custom CSS
* **Computer Vision:** OpenCV, YOLOv8n, EasyOCR, scikit-learn K-Means
* **LLM Engine:** Groq API (Llama 3.3 70B Versatile), Pydantic v2
* **Storage & Analytics:** DuckDB, pandas
* **Quality Assurance:** pytest, ruff, GitHub Actions
* **Deployment:** Docker, Hugging Face Spaces (via Git LFS + orphan branch workflow)

---

## Setup & Installation

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/Bright579523/ai-creative-auditor.git
cd ai-creative-auditor

pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy the template `.env.example` file to `.env` and fill in your Groq API key:
```bash
copy .env.example .env
# Open .env and add your key: GROQ_API_KEY=gsk_xxxxxxx
```

### 3. Initialize Database & Run Batch Pre-processing
Initialize the DuckDB file and run the pipeline to analyze the sample images in `ads_dataset/`:
```bash
python init_db.py
python run_pipeline.py
```

### 4. Run the Streamlit Dashboard
Launch the web interface locally:
```bash
streamlit run app.py
```
The application will automatically open in your default browser at `http://localhost:8501`.

---

## Testing & Quality Control

To run the local unit tests and lint checks:
```bash
pip install pytest ruff
ruff check .           # Check code style and formatting
pytest tests/ -v       # Run the pytest suite
```

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
