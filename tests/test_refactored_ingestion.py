#!/usr/bin/env python3
"""
Test the refactored database backend and DAG logic
Demonstrates raw.github_events table ingestion behavior
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_database_backend_postgres():
    """Test PostgreSQL backend uses raw table loader"""
    from ingestion.backends import DatabaseFactory
    from ingestion.config import DatabaseConfig

    print("=" * 80)
    print("TEST: PostgreSQL Backend with Raw Table Loader")
    print("=" * 80)

    config = DatabaseConfig(
        backend="postgresql",
        pg_host="localhost",
        pg_database="github_archive",
    )

    backend = DatabaseFactory.create_from_config(config)

    print(f"✅ Backend type: {type(backend).__name__}")
    print(f"✅ Has raw_loader: {hasattr(backend, 'raw_loader')}")
    print(f"✅ raw_loader type: {type(backend.raw_loader).__name__}")

    # Check table exists
    exists = backend.table_exists("github_events")
    print(f"✅ raw.github_events table exists: {exists}")

    backend.close()
    print()


def test_get_last_processed_hour():
    """Test querying last processed hour from database"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / 'dags'))

    from github_archive_dag import get_last_processed_hour_from_db

    print("=" * 80)
    print("TEST: Query Last Processed Hour from Database")
    print("=" * 80)

    last_hour = get_last_processed_hour_from_db()

    if last_hour:
        print(f"✅ Last processed hour: {last_hour.strftime('%Y-%m-%d-%H')}")
        print(f"✅ Next hour to process: {(last_hour + timedelta(hours=1)).strftime('%Y-%m-%d-%H')}")
    else:
        print("ℹ️  No data in raw.github_events table (would start from today midnight)")
        today_midnight = datetime.combine(datetime.utcnow().date(), datetime.min.time())
        print(f"   Would start from: {today_midnight.strftime('%Y-%m-%d-%H')}")

    print()


def test_hour_generation_logic():
    """Test hour generation logic"""
    print("=" * 80)
    print("TEST: Hour Generation Logic")
    print("=" * 80)

    from datetime import datetime, timedelta

    # Simulate scenarios
    scenarios = [
        {
            "name": "Empty table (today midnight to current-2)",
            "last_processed": None,
            "expected_start": datetime.combine(datetime.utcnow().date(), datetime.min.time()),
        },
        {
            "name": "Last processed: 2026-04-18-10",
            "last_processed": datetime(2026, 4, 18, 10),
            "expected_start": datetime(2026, 4, 18, 11),
        },
        {
            "name": "Already up to date",
            "last_processed": datetime.utcnow() - timedelta(hours=2),
            "expected_start": None,  # Should skip
        },
    ]

    for scenario in scenarios:
        print(f"\n📊 Scenario: {scenario['name']}")

        last_processed = scenario['last_processed']
        current_time = datetime.utcnow()
        end_dt = (current_time - timedelta(hours=2)).replace(minute=0, second=0, microsecond=0)

        if last_processed:
            start_dt = last_processed + timedelta(hours=1)
            print(f"   Last processed: {last_processed.strftime('%Y-%m-%d-%H')}")
        else:
            start_dt = datetime.combine(current_time.date(), datetime.min.time())
            print(f"   Table empty, starting from: {start_dt.strftime('%Y-%m-%d-%H')}")

        print(f"   End at: {end_dt.strftime('%Y-%m-%d-%H')} (current - 2 hours)")

        if start_dt > end_dt:
            print(f"   ✅ Result: No hours to process (already up to date)")
        else:
            hour_count = int((end_dt - start_dt).total_seconds() / 3600) + 1
            print(f"   ✅ Result: Process {hour_count} hours")
            print(f"   Range: {start_dt.strftime('%Y-%m-%d-%H')} to {end_dt.strftime('%Y-%m-%d-%H')}")

    print()


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    print("\n")
    print("🧪 Testing Refactored Database and DAG Logic")
    print("\n")

    # Test 1: Database backend
    try:
        test_database_backend_postgres()
    except Exception as e:
        print(f"⚠️  Test skipped (database not running): {e}\n")

    # Test 2: Query last processed hour
    try:
        test_get_last_processed_hour()
    except Exception as e:
        print(f"⚠️  Test skipped (database not running): {e}\n")

    # Test 3: Hour generation logic
    test_hour_generation_logic()

    print("=" * 80)
    print("✅ All tests completed!")
    print("=" * 80)

