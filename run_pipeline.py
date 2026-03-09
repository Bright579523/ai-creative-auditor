import os
import glob
import json
from groq import Groq

from vision_ops import analyze_image_vision
from database_ops import save_evaluation_to_db

# ── Groq API Key (set via HF Secrets or .env) ──
api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is not set. Add it to HF Secrets or environment variables.")


def evaluate_with_groq(vision_data, filename):
    """ส่งข้อมูล Vision ให้ Groq LLM วิเคราะห์แล้วคืน JSON"""
    client = Groq()

    prompt = f"""You are a senior creative strategist who has audited over 10,000 ad campaigns
for global brands. You evaluate creatives ruthlessly but fairly — your feedback
is direct, opinionated, and always backed by visual evidence.

CREATIVE BRIEF:
- Filename: {filename}
- People detected: {vision_data['person_count']}
- Dominant colors: {vision_data['dominant_colors']}
- Text found (raw OCR): {vision_data['raw_ocr_text']}

SCORING RUBRIC (use the full range):
- 1-3: Weak — lacks visual hierarchy, unclear message, or poor color choices
- 4-6: Average — functional but forgettable, missing a strong hook
- 7-8: Strong — clear visual impact, good use of color/text, has a focal point
- 9-10: Exceptional — stop-scrolling quality, emotionally compelling, brand-ready

YOUR VOICE:
- Write like a strategist presenting to a CMO: confident, concise, zero fluff.
- Never use filler phrases like "Consider adding", "Try to", or "You might want to".
- Describe colors by their psychological effect (energy, trust, warmth, calm)
  rather than just naming them.
- TEXT CLEANING: The raw OCR often has missing or swapped letters. To correct it:
  1. Look at the VISUAL CONTEXT first — dominant colors, people count, and filename
     all hint at what the ad is about (food, travel, fashion, etc.).
  2. Use that context to pick the most likely correction. For example:
     - "aamen" + food colors (Brown, Orange) + chef → "Ramen" (not "Amen")
     - "santori cam" + travel/ocean colors → "Santorini Calm" (not "cam")
  3. Fix the ENTIRE phrase as a whole, not word-by-word in isolation.
  4. Only output 'None' if the text is truly random characters (e.g. "xkq7 zz#").
- actionable_feedback must be exactly ONE sharp, insight-driven sentence.

Return ONLY valid JSON with these exact keys:
{{
    "corrected_text": "Cleaned text from OCR, or 'None' if unreadable.",
    "design_score": <integer 1-10>,
    "business_score": <integer 1-10>,
    "actionable_feedback": "One direct, strategic sentence."
}}"""

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.8,
            response_format={"type": "json_object"}
        )
        return json.loads(chat_completion.choices[0].message.content)
    except Exception as e:
        print(f"      ⚠️ Groq API Error: {e}")
        return None


def process_ads():
    """Batch pipeline: วิเคราะห์ทุกรูปใน ads_dataset แล้วบันทึกลง DuckDB"""
    image_folder = "ads_dataset"
    valid_extensions = ('.png', '.jpg', '.jpeg')
    image_files = [
        f for f in glob.glob(f"{image_folder}/*.*")
        if f.lower().endswith(valid_extensions)
    ]

    print(f"🚀 Starting pipeline for {len(image_files)} images...\n")

    for index, image_path in enumerate(image_files, start=1):
        filename = os.path.basename(image_path)
        print(f"[{index}/{len(image_files)}] Processing: {filename}")

        try:
            print("   👉 1/3 Scanning image with Vision AI...")
            vision_data = analyze_image_vision(image_path)

            print("   👉 2/3 Sending to Groq AI for evaluation...")
            groq_data = evaluate_with_groq(vision_data, filename)

            if not groq_data:
                print(f"   ❌ Skipped {filename} due to AI error.\n")
                continue

            final_data = {
                "image_filename": filename,
                "person_count": vision_data["person_count"],
                "dominant_colors": vision_data["dominant_colors"],
                "raw_ocr_text": vision_data["raw_ocr_text"],
                "corrected_text": groq_data["corrected_text"],
                "design_score": groq_data["design_score"],
                "business_score": groq_data["business_score"],
                "actionable_feedback": groq_data["actionable_feedback"]
            }

            print("   👉 3/3 Saving to DuckDB...")
            save_evaluation_to_db(final_data)
            print("   ✅ Done!\n")

        except Exception as e:
            print(f"   ❌ Error processing {image_path}: {e}\n")

    print("🎉 Pipeline completed! All data stored in DuckDB.")


if __name__ == "__main__":
    process_ads()