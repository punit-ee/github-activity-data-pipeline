{% macro test_recency(model, column_name, days_back=7) %}

/*
    Custom test: Ensure data is recent (within specified days)
    Useful for monitoring data freshness
*/

select
    max({{ column_name }}) as latest_timestamp,
    current_date - max(date({{ column_name }})) as days_since_latest
from {{ model }}
having days_since_latest > {{ days_back }}

{% endmacro %}

