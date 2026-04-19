{% macro test_event_date_matches_created_at(model, column_name) %}

/*
    Custom test: Ensure event_date matches created_at date
    This validates data integrity in our partitioned table
*/

select
    event_id,
    event_date,
    {{ column_name }} as created_at,
    date({{ column_name }}) as created_date
from {{ model }}
where event_date != date({{ column_name }})

{% endmacro %}

