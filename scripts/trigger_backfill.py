#!/usr/bin/env python3
"""
Helper script to trigger backfill for GitHub Archive DAG.

Usage:
    python scripts/trigger_backfill.py 2026-04-10-00 2026-04-11-23
    python scripts/trigger_backfill.py --start 2026-04-10-00 --end 2026-04-11-23
"""
import argparse
import sys
from datetime import datetime


def validate_date_hour(date_hour_str: str) -> str:
    """Validate date hour format."""
    try:
        datetime.strptime(date_hour_str, "%Y-%m-%d-%H")
        return date_hour_str
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date format: {date_hour_str}. Use YYYY-MM-DD-HH"
        )


def set_airflow_variables(start: str, end: str) -> None:
    """Set Airflow variables for backfill."""
    try:
        from airflow.models import Variable

        Variable.set("github_archive_backfill_start", start)
        Variable.set("github_archive_backfill_end", end)

        print(f"✅ Set backfill range:")
        print(f"   Start: {start}")
        print(f"   End: {end}")

    except ImportError:
        print("❌ Airflow not found. Setting via CLI...")
        import subprocess

        subprocess.run([
            "airflow", "variables", "set",
            "github_archive_backfill_start", start
        ])
        subprocess.run([
            "airflow", "variables", "set",
            "github_archive_backfill_end", end
        ])

        print(f"✅ Set backfill range via CLI:")
        print(f"   Start: {start}")
        print(f"   End: {end}")


def trigger_dag() -> None:
    """Trigger the DAG."""
    try:
        from airflow.api.client.local_client import Client

        client = Client(None, None)
        client.trigger_dag(dag_id='github_archive_pipeline')

        print("✅ DAG triggered successfully!")
        print("\n📍 Monitor progress:")
        print("   Web UI: http://localhost:8080")
        print("   CLI: airflow dags list-runs -d github_archive_pipeline")

    except ImportError:
        print("❌ Airflow API not available. Triggering via CLI...")
        import subprocess

        result = subprocess.run([
            "airflow", "dags", "trigger", "github_archive_pipeline"
        ])

        if result.returncode == 0:
            print("✅ DAG triggered successfully!")
        else:
            print("❌ Failed to trigger DAG")
            sys.exit(1)


def calculate_hours(start: str, end: str) -> int:
    """Calculate number of hours in range."""
    start_dt = datetime.strptime(start, "%Y-%m-%d-%H")
    end_dt = datetime.strptime(end, "%Y-%m-%d-%H")
    return int((end_dt - start_dt).total_seconds() / 3600) + 1


def main():
    parser = argparse.ArgumentParser(
        description="Trigger backfill for GitHub Archive DAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Backfill 2 days of data
  %(prog)s 2026-04-10-00 2026-04-11-23
  
  # Backfill specific hours
  %(prog)s --start 2026-04-15-00 --end 2026-04-15-05
  
  # Backfill last week
  %(prog)s 2026-04-10-00 2026-04-16-23
        """
    )

    parser.add_argument(
        'start',
        nargs='?',
        type=validate_date_hour,
        help='Start date hour (YYYY-MM-DD-HH)'
    )
    parser.add_argument(
        'end',
        nargs='?',
        type=validate_date_hour,
        help='End date hour (YYYY-MM-DD-HH)'
    )
    parser.add_argument(
        '--start',
        dest='start_flag',
        type=validate_date_hour,
        help='Start date hour (YYYY-MM-DD-HH)'
    )
    parser.add_argument(
        '--end',
        dest='end_flag',
        type=validate_date_hour,
        help='End date hour (YYYY-MM-DD-HH)'
    )
    parser.add_argument(
        '--no-trigger',
        action='store_true',
        help='Set variables but do not trigger DAG'
    )

    args = parser.parse_args()

    # Get start and end from either positional or flag arguments
    start = args.start or args.start_flag
    end = args.end or args.end_flag

    if not start or not end:
        parser.error("Both start and end dates are required")

    # Validate range
    start_dt = datetime.strptime(start, "%Y-%m-%d-%H")
    end_dt = datetime.strptime(end, "%Y-%m-%d-%H")

    if start_dt > end_dt:
        parser.error("Start date must be before end date")

    hours = calculate_hours(start, end)

    print("🚀 GitHub Archive Backfill")
    print("=" * 50)
    print(f"Start: {start}")
    print(f"End: {end}")
    print(f"Hours to process: {hours}")
    print("=" * 50)

    # Confirm
    response = input("\nProceed with backfill? (y/N): ")
    if response.lower() != 'y':
        print("❌ Cancelled")
        return

    # Set variables
    set_airflow_variables(start, end)

    # Trigger DAG
    if not args.no_trigger:
        print("\n🎯 Triggering DAG...")
        trigger_dag()
    else:
        print("\n⏸️  Variables set. Trigger DAG manually when ready.")
        print("   airflow dags trigger github_archive_pipeline")


if __name__ == "__main__":
    main()

