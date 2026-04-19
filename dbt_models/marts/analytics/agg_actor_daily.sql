{{
    config(
        materialized='incremental',
        unique_key=['event_date', 'actor_id'],
        tags=['marts', 'curate', 'aggregation']
    )
}}

/*
    Daily aggregation by actor

    Purpose:
    - Track user engagement over time
    - Identify power users
    - Support user analytics

    Source: fct_github_events
    Grain: One row per (event_date, actor_id)
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
        actor_id,
        max(actor_login) as actor_login,
        max(is_bot::int)::boolean as is_bot,

        -- Event counts
        count(*) as total_events,
        count(distinct repo_id) as unique_repositories,
        count(distinct event_type) as unique_event_types,
        count(distinct org_id) as unique_organizations,

        -- Event type breakdown
        sum(case when event_type = 'PushEvent' then 1 else 0 end) as push_events,
        sum(case when event_type = 'PullRequestEvent' then 1 else 0 end) as pull_request_events,
        sum(case when event_type = 'IssuesEvent' then 1 else 0 end) as issue_events,
        sum(case when event_type = 'IssueCommentEvent' then 1 else 0 end) as issue_comment_events,
        sum(case when event_type = 'WatchEvent' then 1 else 0 end) as watch_events,

        -- Activity time distribution
        count(distinct event_hour) as distinct_hours_active,

        -- Metadata
        current_timestamp as dbt_updated_at

    from events

    group by 1, 2

)

select * from aggregated

