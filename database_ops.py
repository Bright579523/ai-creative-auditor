import duckdb

DB_FILE = "ad_database.duckdb"


def save_evaluation_to_db(data: dict, db_path: str = DB_FILE) -> None:
    """Insert one audit record into DuckDB."""
    conn = duckdb.connect(db_path)

    insert_sql = """
    INSERT INTO ad_evaluations (
        image_filename, person_count, dominant_colors,
        raw_ocr_text, corrected_text, design_score,
        business_score, actionable_feedback,
        campaign_type_guess, color_hex_json,
        vision_metrics_json, llm_breakdown_json, pipeline_version
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """

    values = (
        data["image_filename"],
        data["person_count"],
        data["dominant_colors"],
        data["raw_ocr_text"],
        data["corrected_text"],
        data["design_score"],
        data["business_score"],
        data["actionable_feedback"],
        data.get("campaign_type_guess"),
        data.get("color_hex_json"),
        data.get("vision_metrics_json"),
        data.get("llm_breakdown_json"),
        data.get("pipeline_version", "2.0.0"),
    )

    conn.execute(insert_sql, values)
    conn.close()
    print(f"Saved: {data['image_filename']}")
