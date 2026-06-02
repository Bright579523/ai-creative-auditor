"""Migrate existing ad_database.duckdb to schema v2."""

from db.init_db import setup_database

if __name__ == "__main__":
    setup_database()
    print("Migration complete. Re-run: python run_pipeline.py")
