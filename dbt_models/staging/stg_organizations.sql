{{
    config(
        materialized='table',
        tags=['staging', 'conform', 'organizations']
    )
}}

/*
    Staging model for GitHub organizations

    Purpose:
    - Deduplicate organizations from event stream
    - Capture first and last activity timestamps
    - Calculate total events and repositories per organization

    Source: stg_github_events
    Grain: One row per unique organization
*/

with events as (

    select * from {{ ref('stg_github_events') }}
    where org_id is not null
        and org_login is not null

),

organization_aggregates as (

    select
        org_id,
        -- Take the most recent login name
        max(org_login) as org_login,

        -- Activity timeline
        min(created_at) as first_seen_at,
        max(created_at) as last_seen_at,

        -- Activity metrics
        count(*) as total_events,
        count(distinct repo_id) as total_repositories,
        count(distinct actor_id) as unique_contributors,
        count(distinct event_type) as unique_event_types,
        count(distinct event_date) as active_days

    from events

    group by 1

)

select * from organization_aggregates

