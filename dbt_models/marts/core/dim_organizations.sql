{{
    config(
        materialized='table',
        tags=['marts', 'curate', 'dimension']
    )
}}

/*
    Dimension table for GitHub organizations

    Purpose:
    - Provide enriched organization information
    - Support organization-based analytics

    Source: stg_organizations
    Grain: One row per unique organization
    SCD Type: Type 1 (full refresh)
*/

with organizations as (

    select * from {{ ref('stg_organizations') }}

),

enriched as (

    select
        org_id,
        org_login,

        -- Activity timeline
        first_seen_at,
        last_seen_at,

        -- Activity metrics
        total_events,
        total_repositories,
        unique_contributors,
        unique_event_types,
        active_days,

        -- Derived metrics
        round(
            total_events::numeric / nullif(active_days, 0),
            2
        ) as avg_events_per_day,

        round(
            total_events::numeric / nullif(total_repositories, 0),
            2
        ) as avg_events_per_repo,

        -- Metadata
        current_timestamp as dbt_updated_at

    from organizations

)

select * from enriched

