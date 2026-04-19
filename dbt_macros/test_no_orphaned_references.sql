{% macro test_no_orphaned_references(model, column_name, ref_model, ref_column) %}

/*
    Custom test: Ensure no orphaned foreign key references
    Validates referential integrity between models
*/

select
    {{ column_name }}
from {{ model }}
where {{ column_name }} is not null
  and {{ column_name }} not in (
      select {{ ref_column }}
      from {{ ref_model }}
  )

{% endmacro %}

