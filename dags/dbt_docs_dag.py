"""
dbt Documentation Generation DAG

This DAG generates dbt documentation and can be run manually or on a weekly schedule.
It's separated from the main transformation DAG to avoid unnecessary documentation
regeneration on every transformation run.

Schedule: Weekly (Sundays at midnight) or manual trigger
"""

from datetime import datetime, timedelta, timezone

from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator

import logging

logger = logging.getLogger(__name__)


@dag(
    dag_id='dbt_docs_generate',
    description='Generate dbt documentation (run manually or weekly)',
    schedule='0 0 * * 0',  # Run weekly on Sundays at midnight (or trigger manually)
    start_date=datetime(2026, 4, 18),
    catchup=False,
    max_active_runs=1,
    default_args={
        'owner': 'data-team',
        'depends_on_past': False,
        'email': ['data-team@example.com'],
        'email_on_failure': True,
        'email_on_retry': False,
        'retries': 1,
        'retry_delay': timedelta(minutes=5),
        'execution_timeout': timedelta(minutes=30),
    },
    tags=['dbt', 'documentation'],
    doc_md=__doc__,
)
def dbt_docs_generate():
    """
    dbt Documentation Generation

    Generates comprehensive documentation for all dbt models, sources, and tests.
    """

    # Task: Generate documentation
    generate_docs = BashOperator(
        task_id='generate_documentation',
        bash_command="""
        set -e
        cd {{ params.dbt_project_dir }}
        echo "Generating dbt documentation..."
        dbt docs generate \
            --profiles-dir {{ params.profiles_dir }} \
            --target {{ params.target }}
        echo "✅ Documentation generated successfully"
        echo "Documentation files are located in: {{ params.dbt_project_dir }}/dbt_target/"
        """,
        params={
            'dbt_project_dir': '/opt/airflow',
            'profiles_dir': '/opt/airflow',
            'target': 'docker',
        },
    )

    @task()
    def log_completion():
        """Log successful completion of documentation generation"""
        logger.info("✅ dbt documentation generated successfully")
        logger.info("   - Documentation files: dbt_target/index.html, catalog.json, manifest.json")
        logger.info("   - To serve docs: dbt docs serve --profiles-dir /opt/airflow")
        return {
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # Define task dependencies
    generate_docs >> log_completion()


# Instantiate the DAG
dag_instance = dbt_docs_generate()

