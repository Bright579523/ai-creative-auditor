# AI Creative Auditor

> Evaluate advertising creatives with **Computer Vision**, **structured LLM scoring**, and **DuckDB analytics** — built for data-driven marketing decisions.

Upload a poster or ad image and get **Design Score**, **Business Score**, score breakdown, color analytics, WCAG heuristic, and strategic feedback (YOLOv8, EasyOCR, K-Means, Llama 3.3 via Groq).

**[Live demo on Hugging Face Spaces](https://huggingface.co/spaces/Bright87/ai-creative-auditor)**

**[Case study (portfolio)](docs/CASE_STUDY.md)** — problem, KPIs, GDPR, limitations.

---

## Features

| Feature | Technology |
|---------|------------|
| People detection | YOLOv8 |
| Text extraction | EasyOCR (EN + TH) |
| Color analytics | K-Means + HEX + coverage % + psychology tags |
| Accessibility signal | WCAG contrast heuristic on OCR regions |
| AI evaluation | Groq API (Llama 3.3 70B) + Pydantic schema |
| Score breakdown | visual_hierarchy, color_psychology, message_clarity, audience_fit |
| Analytics | DuckDB + Streamlit (distributions, segments, CSV export) |
| A/B comparison | Side-by-side two creatives |

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
├── ui_helpers.py          # Charts, gauges, audit rendering
├── vision_ops.py          # Computer vision pipeline
├── run_pipeline.py        # Groq evaluation + batch pipeline
├── schemas.py             # Pydantic models
├── database_ops.py        # DuckDB writes
├── init_db.py             # Schema v2 setup / migration
├── migrate_db_v2.py       # Run migration helper
├── assets/custom.css      # Streamlit styles
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
