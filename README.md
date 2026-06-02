# AI Creative Auditor

> Evaluate advertising creatives with **Computer Vision**, **structured LLM scoring**, and **DuckDB analytics** — built for data-driven marketing decisions.

Upload a poster or ad image and get **Design Score**, **Business Score**, score breakdown, color analytics, WCAG heuristic, and strategic feedback (YOLOv8, EasyOCR, K-Means, Llama 3.3 via Groq).

**[Live demo on Hugging Face Spaces](https://huggingface.co/spaces/Bright87/ai-creative-auditor)**

**[Case study (portfolio)](docs/CASE_STUDY.md)** — problem, KPIs, GDPR, limitations.

<img width="1880" height="788" alt="image" src="https://github.com/user-attachments/assets/f38578a6-2544-416e-9965-50d5efcd436c" />

⚡ **[Launch the Live Demo on Hugging Face Spaces](https://huggingface.co/spaces/Bright87/ai-creative-auditor)**  
🔒 *Privacy First: Your raw images never leave the host server. The pipeline processes computer vision tasks locally, sending only anonymous metadata to the LLM API.*

---

## Features

### Where it started (V1)
The project began as a simple prototype. Users uploaded a single image, and the system extracted text, counted people, and used an LLM to generate a single design score with a brief feedback block. 

<img width="1542" height="862" alt="image" src="https://github.com/user-attachments/assets/aab5a7e2-a2c0-4059-b929-9a31a3624b48" />


### Why we rebuilt it (V2)
While the prototype worked, it didn't solve real-world problems. Marketers needed to compare assets, designers needed actionable layout feedback, and analysts needed data they could export and query. We updated the architecture to make it a professional-grade portfolio app:

* **Dual-Track Scoring System**: Instead of one generic score, V2 evaluates creatives across two key tracks: **Design Score** and **Business Score**. These are broken down into four distinct categories: Visual Hierarchy, Color Psychology, Message Clarity, and Target Audience Fit.
* **Color Psychology & Extraction**: Moving beyond basic color names, the pipeline uses K-Means Clustering to identify dominant HEX values and their exact canvas coverage %. It then maps these colors to visual psychology tags (e.g., trust, excitement, warmth).
* **Built-in WCAG Contrast Checks**: A helper utility samples the text and background pixels inside OCR boundaries, calculating relative luminance contrast ratios. If your text is hard to read, the system flags it.
* **Side-by-Side A/B Comparisons**: Upload two creatives simultaneously to compare scores, analyze performance delta metrics, and automatically determine a clear winner.
* **Visual Asset Catalog**: The Mock Analytics dashboard features an image gallery pulled directly from DuckDB, allowing teams to filter, search, and visually audit their entire creative library alongside their metrics.

<img width="1554" height="844" alt="image" src="https://github.com/user-attachments/assets/2ba49f23-89a0-4082-89a1-804308cdd35d" />


### Under the Hood (Performance & UI)
* **Instant Startups**: YOLOv8 and EasyOCR models are pre-cached inside the Docker image during the build stage. You no longer have to wait minutes for model weights to download on first run.
* **No Layout Jumps**: Added structural CSS min-height rules and clean fade-in animations to eliminate annoying screen flickering when switching tabs.
* **Stable DB Storage**: Re-architected DuckDB data pipelines to support Git LFS, with custom scripts for deploying binary-heavy histories to Hugging Face Spaces cleanly.

---

## Architecture

```
User Upload → vision_ops (local CV) → Groq LLM (structured JSON) → DuckDB → Streamlit
                  │                         │
                  ├── YOLOv8, EasyOCR       └── Pydantic validation
                  ├── K-Means colors
                  └── WCAG heuristic
```

---

## Project structure

```
├── app.py                 # Streamlit UI (Analyze, A/B, Analytics)
├── core/                  # Configuration and Schemas
│   ├── config.py
│   └── schemas.py
├── vision/                # Computer vision operations
│   └── vision_ops.py
├── pipeline/              # LLM evaluation and batch processing
│   └── run_pipeline.py
├── db/                    # DuckDB database and scripts
│   ├── database_ops.py
│   ├── init_db.py
│   ├── check_db.py
│   └── migrate_db_v2.py
├── ui/                    # Streamlit components
│   └── ui_helpers.py
├── assets/custom.css      # Custom styles
├── docs/CASE_STUDY.md     # Portfolio case study
├── tests/                 # pytest suite
├── notebooks/             # EDA and evaluation notebooks
├── requirements.txt
└── Dockerfile
```

---

## Troubleshooting

**`No module named 'easyocr'`** — install deps, then **restart** Streamlit:

```bash
pip install -r requirements.txt
python check_deps.py
streamlit run app.py
```

**Sideways uploaded photos** — fixed via EXIF auto-rotate in the UI.

**Analytics date error (Thai calendar)** — `created_at` is normalized from Buddhist Era to Gregorian in `app.py`.

---

## Quick start

```bash
git clone https://github.com/Bright579523/ai-creative-auditor.git
cd ai-creative-auditor

pip install -r requirements.txt

# Local API key (auto-loaded from .env — do NOT put secrets in .env.example)
copy .env.example .env
# Edit .env: GROQ_API_KEY=gsk_your_key_here

python init_db.py
python run_pipeline.py   # batch analyze ads_dataset/

streamlit run app.py
```

---

## Tests and lint

```bash
pip install pytest ruff
ruff check schemas.py vision_ops.py run_pipeline.py database_ops.py init_db.py ui_helpers.py tests/
pytest tests/ -v
```

CI runs on push via GitHub Actions (`.github/workflows/ci.yml`).

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Groq API key for LLM evaluation |

See [.env.example](.env.example).

---

## Tech stack

- **UI:** Streamlit, Plotly, custom CSS
- **Vision:** OpenCV, YOLOv8, EasyOCR, scikit-learn
- **AI:** Groq, Llama 3.3 70B, Pydantic v2
- **Data:** DuckDB, pandas
- **Quality:** pytest, ruff, GitHub Actions
- **Deploy:** Docker, Hugging Face Spaces

---

## Portfolio CV bullet (example)

*Built an end-to-end marketing creative audit pipeline combining YOLO, OCR, K-Means color analytics, and structured LLM scoring with DuckDB analytics dashboard (Streamlit, Docker, HF Spaces). Documented GDPR data flow and proxy evaluation metrics for DS/BA stakeholders.*

---

## License

MIT License — see [LICENSE](LICENSE).
