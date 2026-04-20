#!/usr/bin/env python3
"""
Test BigQuery connection and basic operations.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.factory import DatabaseFactory
from ingestion.config import PipelineConfig


def test_connection():
    """Test BigQuery connection and table operations."""
    print("🔍 Testing BigQuery Connection...")
    print("=" * 60)

    config = PipelineConfig.from_env()

    print(f"\n📋 Configuration:")
    print(f"   Backend: {config.database.backend}")
    print(f"   Project: {config.database.bq_project_id}")
    print(f"   Dataset: {config.database.bq_dataset_id}")
    print(f"   Location: {config.database.bq_location}")

    if config.database.backend != "bigquery":
        print("\n❌ Error: DATABASE_BACKEND is not set to 'bigquery'")
        print("   Set: export DATABASE_BACKEND=bigquery")
        return False

    try:
        database = DatabaseFactory.create_from_config(config.database)

        with database:
            print("\n✅ Connection successful!")

            print("\n🔍 Checking if github_events table exists...")
            table_exists = database.table_exists("github_events")

            if table_exists:
                print("✅ Table 'github_events' exists")

                print("\n📊 Querying row count...")
                results = database.execute_query(
                    f"SELECT COUNT(*) as count FROM `{config.database.bq_project_id}.{config.database.bq_dataset_id}.github_events`"
                )

                if results:
                    row_count = results[0].get('count', 0)
                    print(f"   Total rows: {row_count:,}")

                    if row_count > 0:
                        print("\n📅 Checking latest data...")
                        latest = database.execute_query(
                            f"""
                            SELECT 
                                MAX(event_date) as latest_date,
                                COUNT(DISTINCT event_type) as event_types
                            FROM `{config.database.bq_project_id}.{config.database.bq_dataset_id}.github_events`
                            """
                        )

                        if latest:
                            print(f"   Latest date: {latest[0].get('latest_date')}")
                            print(f"   Event types: {latest[0].get('event_types')}")
            else:
                print("⚠️  Table 'github_events' does not exist yet")
                print("   It will be created on first data ingestion")

        print("\n✅ All tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("BigQuery Connection Test")
    print("=" * 60)

    required_vars = [
        "BIGQUERY_PROJECT_ID",
        "GOOGLE_APPLICATION_CREDENTIALS",
    ]

    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print("\n❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nSet these variables and try again.")
        sys.exit(1)

    success = test_connection()
    sys.exit(0 if success else 1)

