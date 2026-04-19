{{
    config(
        materialized='table',
        tags=['staging', 'conform', 'actors']
    )
}}

/*
    Staging model for GitHub actors (users and bots)

    Purpose:
    - Deduplicate actors from event stream
    - Capture first and last activity timestamps
    - Calculate total events per actor
    - Identify bot accounts

    Source: stg_github_events
    Grain: One row per unique actor
*/

with events as (

    select * from {{ ref('stg_github_events') }}

),

actor_aggregates as (

    select
        actor_id,
        -- Take the most recent login name
        max(actor_login) as actor_login,

        -- Bot flag (use max to handle any true value)
        max(is_bot::int)::boolean as is_bot,

        -- Activity timeline
        min(created_at) as first_seen_at,
        max(created_at) as last_seen_at,

        -- Activity metrics
        count(*) as total_events,
        count(distinct event_type) as unique_event_types,
        count(distinct repo_id) as unique_repositories,
        count(distinct event_date) as active_days

    from events

    group by 1

)

select * from actor_aggregates

