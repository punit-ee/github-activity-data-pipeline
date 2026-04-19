{{
    config(
        materialized='table',
        tags=['marts', 'curate', 'dimension']
    )
}}

/*
    Dimension table for GitHub actors

    Purpose:
    - Provide enriched actor information
    - Calculate activity levels
    - Support actor-based analytics

    Source: stg_actors
    Grain: One row per unique actor
    SCD Type: Type 1 (full refresh)
*/

with actors as (

    select * from {{ ref('stg_actors') }}

),

enriched as (

    select
        actor_id,
        actor_login,
        is_bot,

        -- Activity timeline
        first_seen_at,
        last_seen_at,

        -- Activity metrics
        total_events,
        unique_event_types,
        unique_repositories,
        active_days,

        -- Derived metrics
        case
            when total_events >= 10000 then 'very_high'
            when total_events >= 1000 then 'high'
            when total_events >= 100 then 'medium'
            else 'low'
        end as activity_level,

        round(
            total_events::numeric / nullif(active_days, 0),
            2
        ) as avg_events_per_day,

        -- Metadata
        current_timestamp as dbt_updated_at

    from actors

)

select * from enriched

