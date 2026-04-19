{{
    config(
        materialized='table',
        tags=['marts', 'curate', 'dimension']
    )
}}

/*
    Dimension table for GitHub repositories

    Purpose:
    - Provide enriched repository information
    - Calculate popularity tiers
    - Support repository-based analytics

    Source: stg_repositories
    Grain: One row per unique repository
    SCD Type: Type 1 (full refresh)
*/

with repositories as (

    select * from {{ ref('stg_repositories') }}

),

enriched as (

    select
        repo_id,
        repo_name,
        repo_owner,
        repo_slug,

        -- Repository properties
        is_public,
        is_org_owned,

        -- Activity timeline
        first_seen_at,
        last_seen_at,

        -- Activity metrics
        total_events,
        unique_contributors,
        unique_event_types,
        active_days,

        -- Derived metrics
        case
            when total_events >= 100000 then 'viral'
            when total_events >= 10000 then 'high'
            when total_events >= 1000 then 'medium'
            else 'low'
        end as popularity_tier,

        round(
            total_events::numeric / nullif(active_days, 0),
            2
        ) as avg_events_per_day,

        round(
            unique_contributors::numeric / nullif(total_events, 0) * 100,
            2
        ) as contributor_diversity_pct,

        -- Metadata
        current_timestamp as dbt_updated_at

    from repositories

)

select * from enriched

