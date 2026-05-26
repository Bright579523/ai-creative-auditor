import json

import pytest
from pydantic import ValidationError

from run_pipeline import build_record, evaluate_with_groq
from schemas import CreativeAuditResult


def test_creative_audit_result_validation(mock_groq_response):
    result = CreativeAuditResult.model_validate(mock_groq_response)
    assert result.design_score == 7
    assert result.score_breakdown.message_clarity == 7
    d = result.to_legacy_dict()
    assert d["score_breakdown"]["audience_fit"] == 8


def test_creative_audit_rejects_invalid_score():
    bad = {
        "corrected_text": "x",
        "design_score": 11,
        "business_score": 5,
        "actionable_feedback": "ok",
        "score_breakdown": {
            "visual_hierarchy": 5,
            "color_psychology": 5,
            "message_clarity": 5,
            "audience_fit": 5,
        },
    }
    with pytest.raises(ValidationError):
        CreativeAuditResult.model_validate(bad)


def test_build_record(mock_groq_response):
    vision = {
        "person_count": 2,
        "dominant_colors": "Blue, White",
        "raw_ocr_text": "sale",
        "color_analytics": [{"hex": "#0000FF", "name": "Blue", "coverage_pct": 40.0, "psychology": "trust"}],
        "wcag": {"wcag_aa_pass": True, "min_contrast_ratio": 5.0, "regions_checked": 1},
        "processing_ms": 100,
    }
    record = build_record("test.png", vision, mock_groq_response)
    assert record["image_filename"] == "test.png"
    assert record["pipeline_version"] == "2.0.0"
    assert json.loads(record["llm_breakdown_json"])["visual_hierarchy"] == 7


def test_evaluate_with_groq_mock(monkeypatch, mock_groq_response):
    class FakeMessage:
        content = json.dumps(mock_groq_response)

    class FakeChoice:
        message = FakeMessage()

    class FakeCompletion:
        choices = [FakeChoice()]

    class FakeClient:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    return FakeCompletion()

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr("run_pipeline.Groq", lambda api_key=None: FakeClient())

    vision = {
        "person_count": 0,
        "dominant_colors": "Blue",
        "raw_ocr_text": "sale",
        "color_analytics": [],
        "color_insight": "test",
        "wcag": {"wcag_aa_pass": True, "min_contrast_ratio": None, "regions_checked": 0},
    }
    result = evaluate_with_groq(vision, "ad.png")
    assert result is not None
    assert result["design_score"] == 7
