import duckdb


def setup_database():
    """สร้างฐานข้อมูล DuckDB และตาราง ad_evaluations"""
    db_file = "ad_database.duckdb"
    print(f"⏳ Connecting to database: {db_file}...")

    conn = duckdb.connect(db_file)

    # Auto-increment sequence
    conn.sql("CREATE SEQUENCE IF NOT EXISTS seq_ad_id;")

    # Schema ที่ล้อตามโครงสร้าง JSON output ของ pipeline
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
        created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    print("✅ Table 'ad_evaluations' is ready.")

    tables = conn.sql("SHOW TABLES;").fetchall()
    print(f"📋 Current tables: {tables}")

    conn.close()
    print("🔒 Database connection closed.")


if __name__ == "__main__":
    setup_database()