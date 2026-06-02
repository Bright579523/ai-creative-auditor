import json

import duckdb

from db.database_ops import save_evaluation_to_db
from db.init_db import setup_database


def test_save_and_query(tmp_path):
    db_path = str(tmp_path / "test.duckdb")
    setup_database(db_path)

    record = {
        "image_filename": "demo.png",
        "person_count": 1,
        "dominant_colors": "Blue",
        "raw_ocr_text": "hello",
        "corrected_text": "Hello",
        "design_score": 6,
        "business_score": 7,
        "actionable_feedback": "Sharpen the headline.",
        "campaign_type_guess": "tech",
        "color_hex_json": json.dumps([{"hex": "#0000FF", "name": "Blue", "coverage_pct": 50.0, "psychology": "trust"}]),
        "vision_metrics_json": json.dumps({"person_count": 1, "wcag_aa_pass": True}),
        "llm_breakdown_json": json.dumps({"visual_hierarchy": 6, "color_psychology": 7, "message_clarity": 6, "audience_fit": 7}),
        "pipeline_version": "2.0.0",
    }
    save_evaluation_to_db(record, db_path=db_path)

    conn = duckdb.connect(db_path)
    row = conn.execute(
        "SELECT image_filename, design_score, pipeline_version FROM ad_evaluations"
    ).fetchone()
    conn.close()

    assert row[0] == "demo.png"
    assert row[1] == 6
    assert row[2] == "2.0.0"
