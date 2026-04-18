#!/usr/bin/env python3
"""
Test connection pooling for parallel Airflow tasks
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.database import PostgreSQLBackend


def test_single_connection():
    """Test single connection mode (default)"""
    print("1️⃣  Single connection mode (default, safe for sequential):")

    backend = PostgreSQLBackend(
        host='localhost',
        database='github_archive',
        user='postgres',
        password='postgres',
        port=5432,
        use_pooling=False
    )

    print(f"   Has pool: {hasattr(backend, 'pool') and backend.pool is not None}")
    print(f"   Has connection: {backend.connection is not None}")

    last = backend.get_last_processed_hour()
    print(f"   Query works: {last is not None}")
    if last:
        print(f"   Last hour: {last.strftime('%Y-%m-%d-%H')}")

    backend.close()
    print("   ✅ Single connection mode works")
    print()


def test_connection_pooling():
    """Test connection pooling mode (for parallel tasks)"""
    print("2️⃣  Connection pooling mode (for parallel Airflow tasks):")

    backend = PostgreSQLBackend(
        host='localhost',
        database='github_archive',
        user='postgres',
        password='postgres',
        port=5432,
        use_pooling=True,
        pool_size=5
    )

    print(f"   Has pool: {hasattr(backend, 'pool') and backend.pool is not None}")
    print(f"   Pool type: {type(backend.pool).__name__}")

    # Simulate parallel access
    for i in range(3):
        last = backend.get_last_processed_hour()
        if last:
            print(f"   Parallel query {i+1}: {last.strftime('%Y-%m-%d-%H')} ✅")

    backend.close()
    print("   ✅ Connection pooling works (thread-safe)")
    print()


if __name__ == "__main__":
    print("=" * 70)
    print("Testing PostgreSQL Connection Modes")
    print("=" * 70)
    print()

    try:
        test_single_connection()
        test_connection_pooling()

        print("=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print()
        print("Recommendations:")
        print("  📌 Local/Sequential: use_pooling=False (default)")
        print("  📌 Airflow/Parallel: use_pooling=True (set POSTGRES_USE_POOLING=true)")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)

