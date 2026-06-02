import duckdb

DB_FILE = "ad_database.duckdb"


def setup_database(db_path: str = DB_FILE) -> None:
    """Create DuckDB database and ad_evaluations table (schema v2)."""
    print(f"Connecting to database: {db_path}...")
    conn = duckdb.connect(db_path)

    conn.sql("CREATE SEQUENCE IF NOT EXISTS seq_ad_id;")

    conn.sql("""
    CREATE TABLE IF NOT EXISTS ad_evaluations (
        id                  INTEGER DEFAULT nextval('seq_ad_id'),
        image_filename      VARCHAR,
        person_count        INTEGER,
        dominant_colors     VARCHAR,
        raw_ocr_text        VARCHAR,
        corrected_text      VARCHAR,
        design_score        INTEGER,
        business_score      INTEGER,
        actionable_feedback VARCHAR,
        campaign_type_guess VARCHAR,
        color_hex_json      VARCHAR,
        vision_metrics_json VARCHAR,
        llm_breakdown_json  VARCHAR,
        pipeline_version    VARCHAR,
        created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Add v2 columns if table existed from older schema
    new_columns = [
        ("campaign_type_guess", "VARCHAR"),
        ("color_hex_json", "VARCHAR"),
        ("vision_metrics_json", "VARCHAR"),
        ("llm_breakdown_json", "VARCHAR"),
        ("pipeline_version", "VARCHAR"),
    ]
    existing = {row[0] for row in conn.sql("DESCRIBE ad_evaluations").fetchall()}
    for col_name, col_type in new_columns:
        if col_name not in existing:
            conn.sql(f"ALTER TABLE ad_evaluations ADD COLUMN {col_name} {col_type};")
            print(f"Added column: {col_name}")

    print("Table 'ad_evaluations' is ready (schema v2).")
    tables = conn.sql("SHOW TABLES;").fetchall()
    print(f"Current tables: {tables}")
    conn.close()
    print("Database setup complete.")


if __name__ == "__main__":
    setup_database()
