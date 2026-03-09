import cv2
import numpy as np
from sklearn.cluster import KMeans
import logging

# ==========================================
# 1. LAZY MODEL LOADING
# ==========================================
yolo_model = None
ocr_reader = None


def load_models():
    """Lazy import + load: โหลด YOLO และ EasyOCR เฉพาะตอนกด Analyze เท่านั้น"""
    global yolo_model, ocr_reader
    if yolo_model is None:
        from ultralytics import YOLO
        logging.getLogger("ultralytics").setLevel(logging.ERROR)
        yolo_model = YOLO('yolov8n.pt')
    if ocr_reader is None:
        import easyocr
        ocr_reader = easyocr.Reader(['en', 'th'], gpu=False)


# ==========================================
# 2. OBJECT DETECTION & OCR
# ==========================================
def count_people(image_path):
    """นับจำนวนคนในภาพด้วย YOLOv8"""
    load_models()
    results = yolo_model(image_path, classes=[0], verbose=False)
    if results and len(results) > 0:
        return len(results[0].boxes)
    return 0


def extract_text(image_path):
    """อ่านตัวหนังสือในภาพด้วย EasyOCR (ย่อรูปก่อนเพื่อลด Memory)"""
    load_models()
    try:
        img = cv2.imread(image_path)
        if img is None:
            return "No text found"

        max_dim = 500
        h, w = img.shape[:2]
        if max(h, w) > max_dim:
            scale = max_dim / float(max(h, w))
            img = cv2.resize(img, None, fx=scale, fy=scale,
                             interpolation=cv2.INTER_AREA)

        results = ocr_reader.readtext(img, detail=0)
        text = " ".join(results)
        return text if text else "No text found"
    except Exception:
        return "No text found"


# ==========================================
# 3. HSV-BASED COLOR EXTRACTION
# ==========================================
NEUTRAL_COLORS = {'White', 'Light Gray', 'Gray', 'Dark Gray', 'Black'}


def get_color_name_hsv(r, g, b):
    """แปลง RGB → HSV แล้วแมปเป็นชื่อสีที่มนุษย์เข้าใจ

    OpenCV HSV ranges: H 0-179, S 0-255, V 0-255
    ลำดับการตรวจ: Neutral (S/V) → Chromatic (Hue)
    """
    hsv = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2HSV)[0][0]
    h, s, v = int(hsv[0]), int(hsv[1]), int(hsv[2])

    # -- Neutral: Hue ไม่มีความหมายเมื่อ Saturation ต่ำ --
    if v < 35:
        return 'Black'
    if s < 25:
        if v > 210: return 'White'
        if v > 160: return 'Light Gray'
        if v > 90:  return 'Gray'
        return 'Dark Gray'
    if s < 50:
        if v > 200: return 'White'
        if v > 140: return 'Light Gray'
        return 'Gray'

    # -- Chromatic: แบ่งตาม Hue --

    # Red (H 0-8, 165-179)
    if h <= 8 or h >= 165:
        if s < 70 and v > 180: return 'Pink'
        if v < 90:             return 'Dark Red'
        return 'Red'

    # Orange / Brown (H 9-20)
    if 9 <= h <= 20:
        if v < 180 or s < 150: return 'Brown'
        return 'Orange'

    # Yellow-Orange / Brown (H 21-30)
    if 21 <= h <= 30:
        if v < 110: return 'Brown'
        if s < 90:  return 'Light Brown'
        return 'Yellow'

    # Yellow (H 31-38)
    if 31 <= h <= 38:
        if v < 100: return 'Dark Yellow'
        return 'Yellow'

    # Yellow-Green (H 39-50)
    if 39 <= h <= 50:
        if v < 70: return 'Dark Green'
        return 'Green'

    # Green (H 51-85)
    if 51 <= h <= 85:
        if v < 60: return 'Dark Green'
        if s < 80: return 'Light Green'
        return 'Green'

    # Teal / Cyan (H 86-95)
    if 86 <= h <= 95:
        return 'Teal'

    # Sky Blue (H 96-110)
    if 96 <= h <= 110:
        return 'Sky Blue'

    # Blue (H 111-130)
    if 111 <= h <= 130:
        if v < 70: return 'Navy'
        return 'Blue'

    # Purple (H 131-145)
    if 131 <= h <= 145:
        return 'Purple'

    # Pink-Purple (H 146-164)
    if 146 <= h <= 164:
        if s < 90: return 'Light Purple'
        return 'Pink'

    return 'Unknown'


def extract_dominant_colors(image_path, num_colors=4):
    """ดึงสีหลักจากภาพด้วย K-Means แล้วเรียงตามสัดส่วนพิกเซลจริง"""
    image = cv2.imread(image_path)
    if image is None:
        return "Unknown"

    image = cv2.resize(image, (150, 150), interpolation=cv2.INTER_AREA)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pixels = image_rgb.reshape(-1, 3).astype(np.float64)

    kmeans = KMeans(n_clusters=8, random_state=42, n_init=10)
    labels = kmeans.fit_predict(pixels)
    centers = kmeans.cluster_centers_

    # เรียง cluster ตามจำนวนพิกเซลจากมากไปน้อย
    counts = np.bincount(labels)
    sorted_indices = np.argsort(-counts)

    vibrant_list = []
    neutral_list = []

    for idx in sorted_indices:
        r, g, b = int(centers[idx][0]), int(centers[idx][1]), int(centers[idx][2])
        name = get_color_name_hsv(r, g, b)

        if name == 'Unknown':
            continue
        if name in NEUTRAL_COLORS:
            if name not in neutral_list:
                neutral_list.append(name)
        else:
            if name not in vibrant_list:
                vibrant_list.append(name)

    # สีสดขึ้นก่อน ตามด้วย Neutral — ทั้งหมดเรียงตามสัดส่วนจริง
    final_colors = vibrant_list + neutral_list
    return ", ".join(final_colors[:num_colors])


# ==========================================
# 4. MAIN ANALYSIS ENTRY POINT
# ==========================================
def analyze_image_vision(image_path):
    """รวบรวมผลวิเคราะห์ภาพทั้งหมดส่งให้ Pipeline หลัก"""
    return {
        "person_count": count_people(image_path),
        "raw_ocr_text": extract_text(image_path),
        "dominant_colors": extract_dominant_colors(image_path)
    }