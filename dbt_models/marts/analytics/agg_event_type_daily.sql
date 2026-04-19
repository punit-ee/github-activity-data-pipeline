{{
    config(
        materialized='incremental',
        unique_key=['event_date', 'event_type'],
        tags=['marts', 'curate', 'aggregation']
    )
}}

/*
    Daily aggregation by event type

    Purpose:
    - Track event type trends over time
    - Monitor event distribution
    - Support time-series analysis

    Source: fct_github_events
    Grain: One row per (event_date, event_type)
*/

with events as (

    select * from {{ ref('fct_github_events') }}

    {% if is_incremental() %}
    where event_date > (select max(event_date) from {{ this }})
    {% endif %}

),

aggregated as (

    select
        event_date,
        event_type,

        -- Event counts
        count(*) as total_events,
        count(distinct actor_id) as unique_actors,
        count(distinct repo_id) as unique_repositories,
        count(distinct org_id) as unique_organizations,

        -- Bot analysis
        sum(case when is_bot then 1 else 0 end) as bot_events,
        sum(case when not is_bot then 1 else 0 end) as human_events,

        -- Public/private split
        sum(case when is_public then 1 else 0 end) as public_events,
        sum(case when not is_public then 1 else 0 end) as private_events,

        -- Hourly distribution
        count(distinct event_hour) as distinct_hours_active,

        -- Metadata
        current_timestamp as dbt_updated_at

    from events

    group by 1, 2

)

select * from aggregated

