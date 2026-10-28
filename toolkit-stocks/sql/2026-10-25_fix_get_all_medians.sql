-- Fix get_all_medians: function existed with empty signature (no params)
-- but body referenced p_table_fa / p_table_stock / p_stock_industry.
-- PostgREST schema cache could not resolve the 3-arg call -> 500 on
-- /api/stock/financial-analysis/:symbol, watchlist and global-index endpoints.

create or replace function public.get_all_medians(
    p_table_fa text,
    p_table_stock text,
    p_stock_industry text
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
            where s.industry = %L',
            col.column_name, p_table_fa, p_table_stock, p_stock_industry
        )
        into median_value;

        result := result || jsonb_build_object(col.column_name, median_value);
    end loop;

    return result;
end;
$function$;

NOTIFY pgrst, 'reload schema';
