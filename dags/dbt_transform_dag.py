"""
dbt Transformation DAG for GitHub Archive Pipeline

This DAG orchestrates dbt transformations that run after raw data ingestion.
It builds the staging (conform) and marts (curate) layers.

Schedule: Runs every 8 hours
Dependencies: Checks source freshness before transformations
"""

from datetime import datetime, timedelta, timezone

from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator

import logging

logger = logging.getLogger(__name__)


@dag(
    dag_id='dbt_transform_github_archive',
    description='dbt transformations for staging and marts layers',
    schedule='0 */8 * * *',  # Run every 8 hours
    start_date=datetime(2026, 4, 18),
    catchup=False,
    max_active_runs=1,
    default_args={
        'owner': 'data-team',
        'depends_on_past': False,
        'email': ['data-team@example.com'],
        'email_on_failure': True,
        'email_on_retry': False,
        'retries': 2,
        'retry_delay': timedelta(minutes=5),
        'execution_timeout': timedelta(hours=1),
    },
    tags=['dbt', 'transformation', 'staging', 'marts'],
    doc_md=__doc__,
)
def dbt_transform_github_archive():
    """
    dbt Transformation Pipeline

    Flow:
    1. Check source freshness
    2. Run dbt staging models
    3. Test staging models
    4. Run dbt mart models
    5. Test mart models

    Note: dbt deps runs during Docker container startup, not in DAG
    Note: dbt docs generation can be run manually or scheduled separately
    """

    # Task 1: Check source freshness
    dbt_source_freshness = BashOperator(
        task_id='dbt_source_freshness',
        bash_command="""
        cd {{ params.dbt_project_dir }} && \
        dbt source freshness \
            --profiles-dir {{ params.profiles_dir }} \
            --target {{ params.target }}
        """,
        params={
            'dbt_project_dir': '/opt/airflow',
            'profiles_dir': '/opt/airflow',
            'target': 'docker',
        },
    )

    # Task 2: Run dbt staging models (conform layer)
    dbt_run_staging = BashOperator(
        task_id='dbt_run_staging',
        bash_command="""
        cd {{ params.dbt_project_dir }} && \
        dbt run \
            --profiles-dir {{ params.profiles_dir }} \
            --target {{ params.target }} \
            --select staging.* \
            --full-refresh
        """,
        params={
            'dbt_project_dir': '/opt/airflow',
            'profiles_dir': '/opt/airflow',
            'target': 'docker',
        },
    )

    # Task 3: Test staging models
    dbt_test_staging = BashOperator(
        task_id='dbt_test_staging',
        bash_command="""
        cd {{ params.dbt_project_dir }} && \
        dbt test \
            --profiles-dir {{ params.profiles_dir }} \
            --target {{ params.target }} \
            --select staging.*
        """,
        params={
            'dbt_project_dir': '/opt/airflow',
            'profiles_dir': '/opt/airflow',
            'target': 'docker',
        },
    )

    # Task 4: Run dbt mart models (curate layer)
    dbt_run_marts = BashOperator(
        task_id='dbt_run_marts',
        bash_command="""
        cd {{ params.dbt_project_dir }} && \
        dbt run \
            --profiles-dir {{ params.profiles_dir }} \
            --target {{ params.target }} \
            --select marts.*
        """,
        params={
            'dbt_project_dir': '/opt/airflow',
            'profiles_dir': '/opt/airflow',
            'target': 'docker',
        },
    )

    # Task 5: Test mart models
    dbt_test_marts = BashOperator(
        task_id='dbt_test_marts',
        bash_command="""
        cd {{ params.dbt_project_dir }} && \
        dbt test \
            --profiles-dir {{ params.profiles_dir }} \
            --target {{ params.target }} \
            --select marts.*
        """,
        params={
            'dbt_project_dir': '/opt/airflow',
            'profiles_dir': '/opt/airflow',
            'target': 'docker',
        },
    )

    @task()
    def log_completion():
        """Log successful completion of dbt run"""
        logger.info("✅ dbt transformation pipeline completed successfully")
        logger.info("   - Staging models built and tested")
        logger.info("   - Mart models built and tested")
        return {
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # Define task dependencies
    dbt_source_freshness >> dbt_run_staging >> dbt_test_staging
    dbt_test_staging >> dbt_run_marts >> dbt_test_marts >> log_completion()


# Instantiate the DAG
dag_instance = dbt_transform_github_archive()

