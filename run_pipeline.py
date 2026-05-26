import config  # noqa: F401 — loads .env for local dev

import glob
import json
import os

from groq import Groq
from pydantic import ValidationError

from database_ops import save_evaluation_to_db
from schemas import CreativeAuditResult
from vision_ops import PIPELINE_VERSION, analyze_image_vision, color_analytics_to_json

PIPELINE_VERSION_STR = PIPELINE_VERSION


def _build_prompt(vision_data: dict, filename: str) -> str:
    colors_detail = vision_data.get("color_analytics", [])
    colors_str = json.dumps(colors_detail, ensure_ascii=False) if colors_detail else vision_data["dominant_colors"]
    wcag = vision_data.get("wcag", {})
    return f"""You are a senior creative strategist who has audited over 10,000 ad campaigns
for global brands. You evaluate creatives ruthlessly but fairly — your feedback
is direct, opinionated, and always backed by visual evidence.

CREATIVE BRIEF:
- Filename: {filename}
- People detected: {vision_data['person_count']}
- Dominant colors (names): {vision_data['dominant_colors']}
- Color analytics (hex, coverage %, psychology): {colors_str}
- Color insight: {vision_data.get('color_insight', 'N/A')}
- WCAG AA pass (heuristic): {wcag.get('wcag_aa_pass', 'unknown')}
- Min contrast ratio: {wcag.get('min_contrast_ratio', 'N/A')}
- Text found (raw OCR): {vision_data['raw_ocr_text']}

SCORING RUBRIC (use the full range):
- 1-3: Weak — lacks visual hierarchy, unclear message, or poor color choices
- 4-6: Average — functional but forgettable, missing a strong hook
- 7-8: Strong — clear visual impact, good use of color/text, has a focal point
- 9-10: Exceptional — stop-scrolling quality, emotionally compelling, brand-ready

SCORE BREAKDOWN (each 1-10):
- visual_hierarchy: layout, focal point, readability
- color_psychology: palette fit for message and brand
- message_clarity: headline/value prop clarity (use OCR context)
- audience_fit: likely appeal to target segment

YOUR VOICE:
- Write like a strategist presenting to a CMO: confident, concise, zero fluff.
- Never use filler phrases like "Consider adding", "Try to", or "You might want to".
- TEXT CLEANING: Fix OCR using visual context (colors, people, filename). Output 'None' only if unreadable.
- actionable_feedback: exactly ONE sharp, insight-driven sentence.
- campaign_type_guess: short label e.g. food, travel, fashion, tech, retail.

Return ONLY valid JSON with these exact keys:
{{
    "corrected_text": "Cleaned text or 'None'",
    "design_score": <integer 1-10>,
    "business_score": <integer 1-10>,
    "actionable_feedback": "One strategic sentence.",
    "campaign_type_guess": "short category",
    "score_breakdown": {{
        "visual_hierarchy": <integer 1-10>,
        "color_psychology": <integer 1-10>,
        "message_clarity": <integer 1-10>,
        "audience_fit": <integer 1-10>
    }}
}}"""


def evaluate_with_groq(vision_data: dict, filename: str, api_key: str | None = None) -> dict | None:
    """Send vision features to Groq LLM; validate with Pydantic; return dict."""
    key = api_key or os.environ.get("GROQ_API_KEY")
    if not key:
        raise ValueError("GROQ_API_KEY is not set. Add it to HF Secrets or environment variables.")

    client = Groq(api_key=key)
    prompt = _build_prompt(vision_data, filename)

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.8,
            response_format={"type": "json_object"},
        )
        raw = json.loads(chat_completion.choices[0].message.content)
        if "score_breakdown" not in raw:
            raw["score_breakdown"] = {
                "visual_hierarchy": raw.get("design_score", 5),
                "color_psychology": raw.get("design_score", 5),
                "message_clarity": raw.get("business_score", 5),
                "audience_fit": raw.get("business_score", 5),
            }
        result = CreativeAuditResult.model_validate(raw)
        return result.to_legacy_dict()
    except (ValidationError, json.JSONDecodeError, Exception) as e:
        print(f"      Groq API / validation error: {e}")
        return None


def build_record(filename: str, vision_data: dict, groq_data: dict) -> dict:
    """Merge vision + LLM outputs into a DB-ready record."""
    breakdown = groq_data.get("score_breakdown", {})
    wcag = vision_data.get("wcag", {})
    vision_metrics = {
        "person_count": vision_data["person_count"],
        "wcag_aa_pass": wcag.get("wcag_aa_pass"),
        "min_contrast_ratio": wcag.get("min_contrast_ratio"),
        "regions_checked": wcag.get("regions_checked", 0),
        "processing_ms": vision_data.get("processing_ms"),
    }
    return {
        "image_filename": filename,
        "person_count": vision_data["person_count"],
        "dominant_colors": vision_data["dominant_colors"],
        "raw_ocr_text": vision_data["raw_ocr_text"],
        "corrected_text": groq_data["corrected_text"],
        "design_score": groq_data["design_score"],
        "business_score": groq_data["business_score"],
        "actionable_feedback": groq_data["actionable_feedback"],
        "campaign_type_guess": groq_data.get("campaign_type_guess"),
        "color_hex_json": color_analytics_to_json(vision_data.get("color_analytics", [])),
        "vision_metrics_json": json.dumps(vision_metrics),
        "llm_breakdown_json": json.dumps(breakdown),
        "pipeline_version": PIPELINE_VERSION_STR,
    }


def process_ads():
    """Batch pipeline: analyze all images in ads_dataset and save to DuckDB."""
    if not os.environ.get("GROQ_API_KEY"):
        raise ValueError("GROQ_API_KEY is not set. Add it to HF Secrets or environment variables.")

    image_folder = "ads_dataset"
    valid_extensions = (".png", ".jpg", ".jpeg")
    image_files = [
        f for f in glob.glob(f"{image_folder}/*.*")
        if f.lower().endswith(valid_extensions)
    ]

    print(f"Starting pipeline for {len(image_files)} images...\n")

    for index, image_path in enumerate(image_files, start=1):
        filename = os.path.basename(image_path)
        print(f"[{index}/{len(image_files)}] Processing: {filename}")

        try:
            print("   1/3 Vision analysis...")
            vision_data = analyze_image_vision(image_path)

            print("   2/3 Groq evaluation...")
            groq_data = evaluate_with_groq(vision_data, filename)

            if not groq_data:
                print(f"   Skipped {filename} due to AI error.\n")
                continue

            final_data = build_record(filename, vision_data, groq_data)

            print("   3/3 Saving to DuckDB...")
            save_evaluation_to_db(final_data)
            print("   Done.\n")

        except Exception as e:
            print(f"   Error processing {image_path}: {e}\n")

    print("Pipeline completed.")


if __name__ == "__main__":
    process_ads()
