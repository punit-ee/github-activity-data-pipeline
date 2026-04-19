#!/usr/bin/env python3
"""
Metabase Dashboard Setup Script

Automates the creation of dashboards, questions, and database connections
for GitHub Archive analytics.

Usage:
    python metabase/setup_dashboards.py --url http://localhost:3000 \
        --email admin@example.com --password your-password
"""
import argparse
import json
import logging
import sys
import time
from typing import Dict, Any, Optional

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class MetabaseAPI:
    """Simple Metabase API client for dashboard setup."""

    def __init__(self, url: str, email: str, password: str):
        self.base_url = url.rstrip('/')
        self.session = requests.Session()
        self.session_token = None

        # Login
        self._login(email, password)

    def _login(self, email: str, password: str):
        """Authenticate with Metabase."""
        response = self.session.post(
            f"{self.base_url}/api/session",
            json={"username": email, "password": password}
        )
        response.raise_for_status()
        self.session_token = response.json()["id"]
        self.session.headers.update({"X-Metabase-Session": self.session_token})
        logger.info("✅ Authenticated with Metabase")

    def get_database_id(self, name: str = "GitHub Archive") -> Optional[int]:
        """Get database ID by name."""
        response = self.session.get(f"{self.base_url}/api/database")
        response.raise_for_status()
        databases = response.json()["data"]

        for db in databases:
            if db["name"] == name:
                return db["id"]
        return None

    def create_database(self) -> int:
        """Create GitHub Archive database connection."""
        logger.info("Creating database connection...")

        db_config = {
            "name": "GitHub Archive",
            "engine": "postgres",
            "details": {
                "host": "postgres",
                "port": 5432,
                "dbname": "github_archive",
                "user": "postgres",
                "password": "postgres",
                "schema-filters-type": "inclusion",
                "schema-filters-patterns": "marts,staging,raw",
                "additional-options": "searchPath=marts,staging,raw,public&currentSchema=marts",
            },
            "auto_run_queries": True,
            "is_full_sync": True,
        }

        response = self.session.post(
            f"{self.base_url}/api/database",
            json=db_config
        )
        response.raise_for_status()
        db_id = response.json()["id"]

        logger.info(f"✅ Created database connection (ID: {db_id})")

        # Trigger sync
        self.session.post(f"{self.base_url}/api/database/{db_id}/sync_schema")
        logger.info("⏳ Syncing database schema (this may take a minute)...")
        time.sleep(10)

        return db_id

    def create_collection(self, name: str) -> int:
        """Create a collection for organizing dashboards."""
        response = self.session.post(
            f"{self.base_url}/api/collection",
            json={"name": name, "color": "#509EE3"}
        )
        response.raise_for_status()
        collection_id = response.json()["id"]
        logger.info(f"✅ Created collection '{name}' (ID: {collection_id})")
        return collection_id

    def create_question(self, database_id: int, collection_id: int,
                       name: str, sql: str, viz_type: str = "table") -> int:
        """Create a saved question (SQL query)."""
        question = {
            "name": name,
            "display": viz_type,
            "collection_id": collection_id,
            "dataset_query": {
                "type": "native",
                "native": {
                    "query": sql,
                    "template-tags": {}
                },
                "database": database_id
            },
            "visualization_settings": {}
        }

        response = self.session.post(
            f"{self.base_url}/api/card",
            json=question
        )
        response.raise_for_status()
        card_id = response.json()["id"]
        logger.info(f"  ✓ Created question: {name}")
        return card_id

    def create_dashboard(self, collection_id: int, name: str,
                        description: str = "") -> int:
        """Create a dashboard."""
        dashboard = {
            "name": name,
            "description": description,
            "collection_id": collection_id,
        }

        response = self.session.post(
            f"{self.base_url}/api/dashboard",
            json=dashboard
        )
        response.raise_for_status()
        dashboard_id = response.json()["id"]
        logger.info(f"✅ Created dashboard: {name} (ID: {dashboard_id})")
        return dashboard_id


def setup_github_activity_dashboard(api: MetabaseAPI, database_id: int,
                                    collection_id: int):
    """Create GitHub Activity Overview dashboard."""
    logger.info("\n📊 Creating GitHub Activity Overview Dashboard...")

    dashboard_id = api.create_dashboard(
        collection_id,
        "GitHub Activity Overview",
        "Daily trends, event types, and bot vs human activity"
    )

    # Define questions
    questions = [
        {
            "name": "Total Events (Last 30 Days)",
            "sql": """
                SELECT COUNT(*) as total_events
                FROM marts.fct_github_events
                WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
            """,
            "viz_type": "scalar"
        },
        {
            "name": "Daily Event Trend",
            "sql": """
                SELECT event_date, COUNT(*) as events
                FROM marts.fct_github_events
                WHERE event_date >= CURRENT_DATE - INTERVAL '90 days'
                GROUP BY event_date
                ORDER BY event_date
            """,
            "viz_type": "line"
        },
        {
            "name": "Event Type Distribution",
            "sql": """
                SELECT event_type, SUM(total_events) as events
                FROM marts.agg_event_type_daily
                WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY event_type
                ORDER BY events DESC
                LIMIT 10
            """,
            "viz_type": "bar"
        },
        {
            "name": "Bot vs Human Activity",
            "sql": """
                SELECT 
                    event_date,
                    SUM(bot_events) as bot_events,
                    SUM(human_events) as human_events
                FROM marts.agg_event_type_daily
                WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY event_date
                ORDER BY event_date
            """,
            "viz_type": "line"
        },
    ]

    for q in questions:
        api.create_question(
            database_id, collection_id,
            q["name"], q["sql"], q["viz_type"]
        )

    logger.info(f"✅ Dashboard ready: {api.base_url}/dashboard/{dashboard_id}")


def setup_repository_dashboard(api: MetabaseAPI, database_id: int,
                               collection_id: int):
    """Create Repository Analytics dashboard."""
    logger.info("\n📊 Creating Repository Analytics Dashboard...")

    dashboard_id = api.create_dashboard(
        collection_id,
        "Repository Analytics",
        "Top repositories, trending projects, and activity patterns"
    )

    questions = [
        {
            "name": "Top 20 Most Active Repositories",
            "sql": """
                SELECT 
                    repo_name,
                    SUM(total_events) as events,
                    SUM(unique_contributors) as contributors
                FROM marts.agg_repository_daily
                WHERE event_date >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY repo_name
                ORDER BY events DESC
                LIMIT 20
            """,
            "viz_type": "table"
        },
        {
            "name": "Repository Popularity Distribution",
            "sql": """
                SELECT 
                    popularity_tier,
                    COUNT(*) as repository_count
                FROM marts.dim_repositories
                GROUP BY popularity_tier
                ORDER BY 
                    CASE popularity_tier
                        WHEN 'viral' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                    END
            """,
            "viz_type": "pie"
        },
    ]

    for q in questions:
        api.create_question(
            database_id, collection_id,
            q["name"], q["sql"], q["viz_type"]
        )

    logger.info(f"✅ Dashboard ready: {api.base_url}/dashboard/{dashboard_id}")


def setup_developer_dashboard(api: MetabaseAPI, database_id: int,
                              collection_id: int):
    """Create Developer Activity dashboard."""
    logger.info("\n📊 Creating Developer Activity Dashboard...")

    dashboard_id = api.create_dashboard(
        collection_id,
        "Developer Activity",
        "Active developers, contribution patterns, and activity levels"
    )

    questions = [
        {
            "name": "Top 50 Most Active Developers",
            "sql": """
                SELECT 
                    actor_login,
                    SUM(total_events) as total_events,
                    SUM(unique_repositories) as repositories
                FROM marts.agg_actor_daily
                WHERE event_date >= CURRENT_DATE - INTERVAL '7 days'
                    AND is_bot = false
                GROUP BY actor_login
                ORDER BY total_events DESC
                LIMIT 50
            """,
            "viz_type": "table"
        },
        {
            "name": "Activity by Hour of Day",
            "sql": """
                SELECT 
                    event_hour,
                    COUNT(*) as events
                FROM marts.fct_github_events
                WHERE event_date >= CURRENT_DATE - INTERVAL '7 days'
                    AND is_bot = false
                GROUP BY event_hour
                ORDER BY event_hour
            """,
            "viz_type": "bar"
        },
    ]

    for q in questions:
        api.create_question(
            database_id, collection_id,
            q["name"], q["sql"], q["viz_type"]
        )

    logger.info(f"✅ Dashboard ready: {api.base_url}/dashboard/{dashboard_id}")


def main():
    parser = argparse.ArgumentParser(description="Setup Metabase dashboards")
    parser.add_argument("--url", default="http://localhost:3000",
                       help="Metabase URL")
    parser.add_argument("--email", required=True,
                       help="Admin email")
    parser.add_argument("--password", required=True,
                       help="Admin password")

    args = parser.parse_args()

    try:
        # Initialize API client
        api = MetabaseAPI(args.url, args.email, args.password)

        # Check if database exists, create if not
        db_id = api.get_database_id()
        if not db_id:
            db_id = api.create_database()
        else:
            logger.info(f"✅ Using existing database connection (ID: {db_id})")

        # Create collection for dashboards
        collection_id = api.create_collection("GitHub Archive Analytics")

        # Create dashboards
        setup_github_activity_dashboard(api, db_id, collection_id)
        setup_repository_dashboard(api, db_id, collection_id)
        setup_developer_dashboard(api, db_id, collection_id)

        logger.info("\n" + "="*60)
        logger.info("✅ Metabase dashboards setup complete!")
        logger.info(f"🌐 Access dashboards at: {args.url}")
        logger.info("="*60)

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ API request failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

