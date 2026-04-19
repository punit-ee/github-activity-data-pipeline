{{
    config(
        materialized='incremental',
        unique_key=['event_id', 'event_date'],
        partition_by={
            "field": "event_date",
            "data_type": "date",
            "granularity": "day"
        },
        cluster_by=['event_type', 'repo_id', 'actor_id'],
        tags=['marts', 'curate', 'fact']
    )
}}

/*
    Fact table for GitHub events

    Purpose:
    - Denormalized event data for fast querying
    - Incremental loading for performance
    - Partitioned by date, clustered by key dimensions

    Source: stg_github_events
    Grain: One row per event
*/

with events as (

    select * from {{ ref('stg_github_events') }}

    {% if is_incremental() %}
    -- Only load new data on incremental runs
    where event_date > (SELECT COALESCE(MAX(event_date), '2026-04-12'::date) from {{ this }})
    {% endif %}

),

repositories as (

    select
        repo_id,
        repo_owner,
        repo_slug
    from {{ ref('stg_repositories') }}

),

final as (

    select
        -- Primary keys
        e.event_id,
        e.event_date,

        -- Event attributes
        e.event_type,
        e.created_at,
        e.event_hour,
        e.event_day_of_week,
        e.event_year,
        e.event_month,
        e.event_day,

        -- Actor dimension
        e.actor_id,
        e.actor_login,
        e.is_bot,

        -- Repository dimension
        e.repo_id,
        e.repo_name,
        r.repo_owner,
        r.repo_slug,

        -- Organization dimension
        e.org_id,
        e.org_login,

        -- Event properties
        e.is_public,
        e.payload,

        -- Lineage
        e.source_file,
        e.ingested_at,
        current_timestamp as dbt_updated_at

    from events e
    left join repositories r
        on e.repo_id = r.repo_id

)

select * from final

