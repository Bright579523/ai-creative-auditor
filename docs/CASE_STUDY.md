# Case Study: AI Creative Auditor

## Problem

Marketing teams review dozens of ad creatives per campaign. Manual review is slow, subjective, and hard to benchmark across channels. Stakeholders need a fast, consistent first pass on **design quality**, **commercial potential**, and **accessibility risk** before A/B tests or media spend.

## Stakeholders

| Role | Need |
|------|------|
| Marketing manager | Rank creatives, spot weak assets early |
| Brand / design | Color psychology, hierarchy, readability |
| Compliance / accessibility | Text contrast heuristics (WCAG-oriented signal) |
| Data / analytics | Exportable history in SQL-friendly storage |

## Solution

End-to-end pipeline:

1. **Local computer vision** (privacy-friendly): YOLOv8 people count, EasyOCR text, K-Means color analytics with HEX and coverage %, heuristic WCAG contrast on OCR regions.
2. **Structured LLM evaluation** (Groq / Llama 3.3): Pydantic-validated JSON with design/business scores and a four-dimension breakdown.
3. **DuckDB warehouse** + **Streamlit dashboard**: KPIs, distributions, segmentation, CSV export, A/B comparison.

```
Upload → vision_ops (local) → Groq (metadata + text) → DuckDB → Analytics UI
```

## Methods

| Component | Technique | Output |
|-----------|-----------|--------|
| Objects | YOLOv8n, class 0 (person) | `person_count` |
| Text | EasyOCR (EN, TH) | `raw_ocr_text` + OCR boxes for contrast |
| Colors | K-Means (k=8) + HSV naming | HEX, coverage %, psychology tag |
| Accessibility | Luminance contrast on OCR regions | `wcag_aa_pass`, min ratio |
| Scoring | Llama 3.3 70B via Groq, JSON schema | Scores 1–10 + breakdown + feedback |

**Why hybrid?** Images stay on the client/server for CV; only derived features and OCR text go to the LLM—lower cost, faster iteration, and clearer GDPR story than sending full images to a third party by default.

## Sample KPIs (from DuckDB analytics)

Illustrative metrics exposed in the app:

| KPI | Definition |
|-----|------------|
| Ads analyzed | Row count in `ad_evaluations` |
| Avg design / business score | Mean of LLM scores |
| Low performers | `design_score + business_score < 12` |
| Top quartile | Design score > 8 |
| Color psychology mix | Dominant tag from `color_hex_json` |
| Segment by people count | Mean scores grouped by `person_count` |

Re-run `python run_pipeline.py` after adding images to `ads_dataset/` to refresh benchmarks.

## Validation approach (no ground-truth labels)

LLM scores are **proxy metrics**, not certified creative research:

- **OCR correction rate**: share of rows where `corrected_text != raw_ocr_text` and not `None` (see `notebooks/02_model_evaluation.ipynb`).
- **Score distribution**: histograms to detect collapse (e.g. all 7–8).
- **Human spot-check**: 10–20 ads with manual thumbs up/down on feedback plausibility.
- **Stability**: re-run same image twice; note variance from temperature=0.8.

Do not claim “90% accuracy” without labeled evaluation data.

## GDPR and data processing

| Data | Where processed | Sent externally? |
|------|-----------------|------------------|
| Raw image | Local (OpenCV, YOLO, EasyOCR) | No (default pipeline) |
| OCR text, counts, colors | Aggregated features | Yes — to Groq API as prompt text |
| Scores & feedback | Groq response | Stored locally in DuckDB |

- No PII fields are collected by design.
- For EU deployments: document Groq as sub-processor, use API terms/DPA, and consider EU hosting or on-prem LLM if required.
- API keys via environment variables only (see `.env.example`).

## Limitations

- OCR weak on German text (model trained EN/TH); DE campaigns need PaddleOCR or similar later.
- WCAG check is **heuristic** on OCR boxes, not a full accessibility audit.
- LLM scores are subjective and temperature-dependent.
- YOLO counts people only; products/logos need separate detectors.

## Next steps

- Labeled evaluation set with human scores for calibration.
- Optional vision LLM for ambiguous OCR only.
- Campaign-level rollups (brand, channel) in DuckDB.
- German OCR language pack for DACH market.

## Tech stack

Python 3.10 · Streamlit · Plotly · DuckDB · OpenCV · YOLOv8 · EasyOCR · scikit-learn · Groq · Pydantic · pytest · Docker · Hugging Face Spaces
