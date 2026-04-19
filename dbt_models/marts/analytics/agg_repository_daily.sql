{{
    config(
        materialized='incremental',
        unique_key=['event_date', 'repo_id'],
        tags=['marts', 'curate', 'aggregation']
    )
}}

/*
    Daily aggregation by repository

    Purpose:
    - Track repository activity trends
    - Identify trending repositories
    - Support repository analytics

    Source: fct_github_events
    Grain: One row per (event_date, repo_id)
*/

with events as (

    select * from {{ ref('fct_github_events') }}
    where repo_id is not null

    {% if is_incremental() %}
    and event_date > (SELECT COALESCE(MAX(event_date), '2026-04-12'::date) from {{ this }})
    {% endif %}

),

aggregated as (

    select
        event_date,
        repo_id,
        max(repo_name) as repo_name,
        max(repo_owner) as repo_owner,
        max(repo_slug) as repo_slug,

        -- Event counts
        count(*) as total_events,
        count(distinct actor_id) as unique_contributors,
        count(distinct event_type) as unique_event_types,

        -- Event type breakdown
        sum(case when event_type = 'PushEvent' then 1 else 0 end) as push_events,
        sum(case when event_type = 'PullRequestEvent' then 1 else 0 end) as pull_request_events,
        sum(case when event_type = 'IssuesEvent' then 1 else 0 end) as issue_events,
        sum(case when event_type = 'IssueCommentEvent' then 1 else 0 end) as issue_comment_events,
        sum(case when event_type = 'WatchEvent' then 1 else 0 end) as watch_events,
        sum(case when event_type = 'ForkEvent' then 1 else 0 end) as fork_events,

        -- Bot analysis
        sum(case when is_bot then 1 else 0 end) as bot_events,
        sum(case when not is_bot then 1 else 0 end) as human_events,

        -- Metadata
        current_timestamp as dbt_updated_at

    from events

    group by 1, 2

)

select * from aggregated

