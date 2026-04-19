{{
    config(
        materialized='incremental',
        unique_key=['event_id', 'event_date'],
        tags=['staging', 'conform', 'events']
    )
}}

/*
    Staging model for GitHub events

    Purpose:
    - Clean and standardize raw event data
    - Add derived fields (is_bot, time dimensions)
    - Ensure data quality with null handling
    - Prepare data for downstream marts

    Source: raw.github_events (partitioned by event_date)
    Grain: One row per event (unique on event_id + event_date)
*/

with source as (

    select * from {{ source('raw', 'github_events') }}

    {% if is_incremental() %}
    -- Only load new data on incremental runs
    where event_date > (select max(event_date) from {{ this }})
    {% endif %}

),

cleaned as (

    select
        -- Primary keys
        event_id,
        event_date,

        -- Event metadata
        event_type,
        created_at,

        -- Actor (user)
        actor_id,
        actor_login,

        -- Repository
        repo_id,
        repo_name,

        -- Organization
        org_id,
        org_login,

        -- Event properties
        is_public,
        payload,

        -- Lineage
        source_file,
        ingested_at,
        updated_at

    from source

    -- Data quality filters
    where 1=1
        and event_id is not null
        and event_type is not null
        and created_at is not null
        and actor_id is not null
        and actor_login is not null
        -- Filter out deleted events if configured
        {% if var('excluded_event_types', []) %}
        and event_type not in ({{ "'" + "','".join(var('excluded_event_types')) + "'" }})
        {% endif %}

),

enriched as (

    select
        *,

        -- Bot detection (common bot patterns)
        case
            when lower(actor_login) like '%[bot]%' then true
            when lower(actor_login) like '%dependabot%' then true
            when lower(actor_login) like '%github-actions%' then true
            when lower(actor_login) like '%renovate%' then true
            when lower(actor_login) like '%greenkeeper%' then true
            else false
        end as is_bot,

        -- Time dimensions
        extract(hour from created_at) as event_hour,
        extract(dow from created_at) + 1 as event_day_of_week,  -- 1=Monday, 7=Sunday
        extract(year from created_at) as event_year,
        extract(month from created_at) as event_month,
        extract(day from created_at) as event_day

    from cleaned

)

select * from enriched

