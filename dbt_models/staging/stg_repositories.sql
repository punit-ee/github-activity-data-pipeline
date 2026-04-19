{{
    config(
        materialized='table',
        tags=['staging', 'conform', 'repositories']
    )
}}

/*
    Staging model for GitHub repositories

    Purpose:
    - Deduplicate repositories from event stream
    - Extract owner and repository name components
    - Capture first and last activity timestamps
    - Calculate total events per repository
    - Identify organization-owned repositories

    Source: stg_github_events
    Grain: One row per unique repository
*/

with events as (

    select * from {{ ref('stg_github_events') }}
    where repo_id is not null
        and repo_name is not null

),

repository_aggregates as (

    select
        repo_id,
        -- Take the most recent repo name
        max(repo_name) as repo_name,

        -- Extract owner and repository components from most recent name
        split_part(max(repo_name), '/', 1) as repo_owner,
        split_part(max(repo_name), '/', 2) as repo_slug,

        -- Repository properties
        max(is_public::int)::boolean as is_public,

        -- Organization ownership (if org_id exists for this repo)
        max(case when org_id is not null then 1 else 0 end)::boolean as is_org_owned,

        -- Activity timeline
        min(created_at) as first_seen_at,
        max(created_at) as last_seen_at,

        -- Activity metrics
        count(*) as total_events,
        count(distinct actor_id) as unique_contributors,
        count(distinct event_type) as unique_event_types,
        count(distinct event_date) as active_days

    from events

    group by 1

)

select * from repository_aggregates

