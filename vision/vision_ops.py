import json
import logging
import time
from typing import Any

import cv2
import numpy as np
from sklearn.cluster import KMeans

PIPELINE_VERSION = "2.0.0"

# ==========================================
# 1. LAZY MODEL LOADING
# ==========================================
yolo_model = None
ocr_reader = None

NEUTRAL_COLORS = {"White", "Light Gray", "Gray", "Dark Gray", "Black"}

COLOR_PSYCHOLOGY = {
    "Red": "energy",
    "Dark Red": "energy",
    "Orange": "energy",
    "Yellow": "energy",
    "Dark Yellow": "energy",
    "Pink": "warmth",
    "Brown": "warmth",
    "Light Brown": "warmth",
    "Blue": "trust",
    "Navy": "trust",
    "Sky Blue": "trust",
    "Teal": "trust",
    "Green": "calm",
    "Light Green": "calm",
    "Dark Green": "calm",
    "Purple": "calm",
    "Light Purple": "calm",
    "White": "trust",
    "Light Gray": "trust",
    "Gray": "trust",
    "Dark Gray": "trust",
    "Black": "trust",
}


def load_ocr_reader():
    """Lazy-load EasyOCR only (no YOLO)."""
    global ocr_reader
    if ocr_reader is None:
        import easyocr

        ocr_reader = easyocr.Reader(["en", "th"], gpu=False)


def load_models():
    """Lazy-load YOLO and EasyOCR when full analysis runs."""
    global yolo_model
    load_ocr_reader()
    if yolo_model is None:
        from ultralytics import YOLO

        logging.getLogger("ultralytics").setLevel(logging.ERROR)
        yolo_model = YOLO("yolov8n.pt")


# ==========================================
# 2. OBJECT DETECTION & OCR
# ==========================================
def _resize_for_ocr(img: np.ndarray, max_dim: int = 500) -> np.ndarray:
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / float(max(h, w))
        return cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    return img


def count_people(image_path: str) -> int:
    """Count people in image using YOLOv8 (class 0)."""
    load_models()
    results = yolo_model(image_path, classes=[0], verbose=False)
    if results and len(results) > 0:
        return len(results[0].boxes)
    return 0


def extract_text(image_path: str) -> str:
    """Extract text with EasyOCR (image resized to reduce memory)."""
    load_ocr_reader()
    try:
        img = cv2.imread(image_path)
        if img is None:
            return "No text found"
        img = _resize_for_ocr(img)
        results = ocr_reader.readtext(img, detail=0)
        text = " ".join(results)
        return text if text else "No text found"
    except Exception:
        return "No text found"


def extract_text_with_boxes(image_path: str) -> list[dict[str, Any]]:
    """OCR with bounding boxes for contrast checks."""
    load_ocr_reader()
    try:
        img = cv2.imread(image_path)
        if img is None:
            return []
        img = _resize_for_ocr(img)
        results = ocr_reader.readtext(img, detail=1)
        boxes = []
        for item in results:
            if len(item) < 3:
                continue
            bbox, text, conf = item[0], item[1], item[2]
            if conf < 0.3 or not str(text).strip():
                continue
            pts = np.array(bbox, dtype=np.int32)
            x1, y1 = pts.min(axis=0)
            x2, y2 = pts.max(axis=0)
            boxes.append({"text": text, "bbox": (int(x1), int(y1), int(x2), int(y2))})
        return boxes
    except Exception:
        return []


# ==========================================
# 3. HSV COLOR NAMING & K-MEANS ANALYTICS
# ==========================================
def get_color_name_hsv(r: int, g: int, b: int) -> str:
    """Map RGB to human-readable color name via HSV rules."""
    hsv = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2HSV)[0][0]
    h, s, v = int(hsv[0]), int(hsv[1]), int(hsv[2])

    if v < 35:
        return "Black"
    if s < 25:
        if v > 210:
            return "White"
        if v > 160:
            return "Light Gray"
        if v > 90:
            return "Gray"
        return "Dark Gray"
    if s < 50:
        if v > 200:
            return "White"
        if v > 140:
            return "Light Gray"
        return "Gray"

    if h <= 8 or h >= 165:
        if s < 70 and v > 180:
            return "Pink"
        if v < 90:
            return "Dark Red"
        return "Red"
    if 9 <= h <= 20:
        if v < 180 or s < 150:
            return "Brown"
        return "Orange"
    if 21 <= h <= 30:
        if v < 110:
            return "Brown"
        if s < 90:
            return "Light Brown"
        return "Yellow"
    if 31 <= h <= 38:
        if v < 100:
            return "Dark Yellow"
        return "Yellow"
    if 39 <= h <= 50:
        if v < 70:
            return "Dark Green"
        return "Green"
    if 51 <= h <= 85:
        if v < 60:
            return "Dark Green"
        if s < 80:
            return "Light Green"
        return "Green"
    if 86 <= h <= 95:
        return "Teal"
    if 96 <= h <= 110:
        return "Sky Blue"
    if 111 <= h <= 130:
        if v < 70:
            return "Navy"
        return "Blue"
    if 131 <= h <= 145:
        return "Purple"
    if 146 <= h <= 164:
        if s < 90:
            return "Light Purple"
        return "Pink"
    return "Unknown"


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02X}{g:02X}{b:02X}"


def psychology_for_color(name: str) -> str:
    return COLOR_PSYCHOLOGY.get(name, "trust")


def extract_color_analytics(image_path: str, num_colors: int = 4) -> list[dict[str, Any]]:
    """K-Means color clusters with HEX, coverage %, and psychology tags."""
    image = cv2.imread(image_path)
    if image is None:
        return []

    image = cv2.resize(image, (150, 150), interpolation=cv2.INTER_AREA)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pixels = image_rgb.reshape(-1, 3).astype(np.float64)
    total_pixels = len(pixels)

    kmeans = KMeans(n_clusters=8, random_state=42, n_init=10)
    labels = kmeans.fit_predict(pixels)
    centers = kmeans.cluster_centers_
    counts = np.bincount(labels, minlength=8)
    sorted_indices = np.argsort(-counts)

    seen_names: set[str] = set()
    results: list[dict[str, Any]] = []

    for idx in sorted_indices:
        if len(results) >= num_colors:
            break
        r, g, b = int(centers[idx][0]), int(centers[idx][1]), int(centers[idx][2])
        name = get_color_name_hsv(r, g, b)
        if name == "Unknown" or name in seen_names:
            continue
        seen_names.add(name)
        coverage_pct = round(100.0 * counts[idx] / total_pixels, 1)
        results.append(
            {
                "hex": rgb_to_hex(r, g, b),
                "name": name,
                "coverage_pct": coverage_pct,
                "psychology": psychology_for_color(name),
            }
        )
    return results


def extract_dominant_colors(image_path: str, num_colors: int = 4) -> str:
    """Comma-separated dominant color names (backward compatible)."""
    analytics = extract_color_analytics(image_path, num_colors=num_colors)
    if not analytics:
        return "Unknown"
    return ", ".join(c["name"] for c in analytics)


def color_insight_sentence(colors: list[dict[str, Any]]) -> str:
    """One-line business insight from dominant color psychology."""
    if not colors:
        return "Insufficient color signal for psychology mapping."
    top = colors[0]
    tags = [c["psychology"] for c in colors[:3]]
    dominant_tag = max(set(tags), key=tags.count)
    return (
        f"Dominant palette ({top['name']} at {top['coverage_pct']}%) "
        f"signals {dominant_tag} — align copy and CTA with this tone."
    )


# ==========================================
# 4. WCAG CONTRAST (HEURISTIC ON OCR REGIONS)
# ==========================================
def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = [x / 255.0 for x in rgb]

    def channel(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = channel(r), channel(g), channel(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(c1: tuple[int, int, int], c2: tuple[int, int, int]) -> float:
    l1, l2 = _relative_luminance(c1), _relative_luminance(c2)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _median_rgb(region: np.ndarray) -> tuple[int, int, int]:
    if region.size == 0:
        return (128, 128, 128)
    med = np.median(region.reshape(-1, 3), axis=0)
    return int(med[0]), int(med[1]), int(med[2])


def check_wcag_contrast(image_path: str) -> dict[str, Any]:
    """
    Heuristic WCAG AA check on OCR text regions.
    Samples text bbox vs padded surrounding area.
    """
    img = cv2.imread(image_path)
    if img is None:
        return {"wcag_aa_pass": False, "min_contrast_ratio": 0.0, "regions_checked": 0}

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w = img_rgb.shape[:2]
    boxes = extract_text_with_boxes(image_path)

    if not boxes:
        return {"wcag_aa_pass": True, "min_contrast_ratio": None, "regions_checked": 0}

    ratios: list[float] = []
    for box in boxes:
        x1, y1, x2, y2 = box["bbox"]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x2 <= x1 or y2 <= y1:
            continue
        pad = 8
        bx1, by1 = max(0, x1 - pad), max(0, y1 - pad)
        bx2, by2 = min(w, x2 + pad), min(h, y2 + pad)
        text_rgb = _median_rgb(img_rgb[y1:y2, x1:x2])
        surround = img_rgb[by1:by2, bx1:bx2]
        bg_rgb = _median_rgb(surround)
        ratios.append(_contrast_ratio(text_rgb, bg_rgb))

    if not ratios:
        return {"wcag_aa_pass": True, "min_contrast_ratio": None, "regions_checked": 0}

    min_ratio = round(min(ratios), 2)
    return {
        "wcag_aa_pass": min_ratio >= 4.5,
        "min_contrast_ratio": min_ratio,
        "regions_checked": len(ratios),
    }


# ==========================================
# 5. MAIN ENTRY POINT
# ==========================================
def analyze_image_vision(image_path: str) -> dict[str, Any]:
    """Full local vision analysis for the audit pipeline."""
    start = time.perf_counter()
    colors = extract_color_analytics(image_path)
    wcag = check_wcag_contrast(image_path)
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    return {
        "person_count": count_people(image_path),
        "raw_ocr_text": extract_text(image_path),
        "dominant_colors": extract_dominant_colors(image_path),
        "color_analytics": colors,
        "color_insight": color_insight_sentence(colors),
        "wcag": wcag,
        "processing_ms": elapsed_ms,
        "pipeline_version": PIPELINE_VERSION,
    }


def color_analytics_to_json(colors: list[dict[str, Any]]) -> str:
    return json.dumps(colors, ensure_ascii=False)
