import duckdb


def save_evaluation_to_db(data):
    """บันทึกผลการวิเคราะห์ 1 รายการลง DuckDB"""
    conn = duckdb.connect("ad_database.duckdb")

    insert_sql = """
    INSERT INTO ad_evaluations (
        image_filename, person_count, dominant_colors,
        raw_ocr_text, corrected_text, design_score,
        business_score, actionable_feedback
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """

    values = (
        data['image_filename'], data['person_count'], data['dominant_colors'],
        data['raw_ocr_text'], data['corrected_text'], data['design_score'],
        data['business_score'], data['actionable_feedback']
    )

    conn.execute(insert_sql, values)
    conn.close()
    print(f"💾 Saved: {data['image_filename']}")