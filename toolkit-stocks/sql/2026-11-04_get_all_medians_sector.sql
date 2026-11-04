-- Fix get_all_medians after the sector/industry convention switch
-- (DB now uses standard GICS naming: stock.sector = broad grouping,
-- stock.industry = fine-grained).
--
-- The body was already updated to filter s.sector, but the signature
-- still declared p_stock_industry -> runtime error
-- 'column "p_stock_sector" does not exist' on every call.
-- Rename the parameter to match the body and the new convention.
-- Postgres cannot rename a plpgsql input parameter in-place -> drop first.

drop function if exists public.get_all_medians(text, text, text);

create or replace function public.get_all_medians(
    p_table_fa text,
    p_table_stock text,
    p_stock_sector text
)
returns jsonb
language plpgsql
as $function$
declare
    col record;
    median_value numeric;
    result jsonb := '{}';
begin
    for col in
        select column_name
        from information_schema.columns
        where table_schema = 'public'
          and table_name = p_table_fa
          and data_type in ('integer', 'numeric', 'real', 'double precision')
    loop
        execute format(
            'select percentile_cont(0.5) within group (order by fa.%I)
            from %I fa
            join %I s on s.id = fa.stock_id
            where s.sector = %L',
            col.column_name, p_table_fa, p_table_stock, p_stock_sector
        )
        into median_value;
    result := result || jsonb_build_object(col.column_name, median_value);
    end loop;

    return result;
end;
$function$;

NOTIFY pgrst, 'reload schema';
