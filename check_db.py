import duckdb


def check_database():
    """ตรวจสอบข้อมูลในฐานข้อมูลแบบเร็ว"""
    conn = duckdb.connect('ad_database.duckdb')

    total_rows = conn.execute("SELECT COUNT(*) FROM ad_evaluations").fetchone()[0]
    print(f"📦 Total records: {total_rows}\n")

    print("📊 Sample (first 3 rows):")
    sample_data = conn.execute("""
        SELECT image_filename, design_score, business_score, actionable_feedback
        FROM ad_evaluations
        LIMIT 3
    """).fetchall()

    for row in sample_data:
        print(f"  👉 File: {row[0]}")
        print(f"     🎨 Design: {row[1]}/10")
        print(f"     💼 Business: {row[2]}/10")
        print(f"     💡 Feedback: {row[3]}\n")

    conn.close()


if __name__ == "__main__":
    check_database()