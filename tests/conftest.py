import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture
def sample_image(tmp_path):
    """Small solid-color image for vision tests (no YOLO/OCR load)."""
    cv2 = pytest.importorskip("cv2")
    import numpy as np

    img = np.zeros((80, 120, 3), dtype=np.uint8)
    img[:, :] = (40, 80, 200)  # BGR bluish
    path = tmp_path / "sample.png"
    cv2.imwrite(str(path), img)
    return str(path)


@pytest.fixture
def mock_groq_response():
    return {
        "corrected_text": "Summer Sale",
        "design_score": 7,
        "business_score": 8,
        "actionable_feedback": "Lead with the discount in the hero zone.",
        "campaign_type_guess": "retail",
        "score_breakdown": {
            "visual_hierarchy": 7,
            "color_psychology": 8,
            "message_clarity": 7,
            "audience_fit": 8,
        },
    }
