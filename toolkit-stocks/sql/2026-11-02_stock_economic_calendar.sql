-- stock_economic_calendar: normalized Yahoo calendar events (earnings,
-- economic releases) keyed for upsert. Pipeline-internal reference data;
-- RLS is enabled and public reads are allowed so future UI endpoints can
-- query it without service-role credentials.
create table if not exists stock_economic_calendar (
	id               bigint generated always as identity primary key,
	event_type       text        not null,
	symbol           text,
	stock_id         bigint      references stock(id) on delete set null,
	region           text        not null,
	event_name       text,
	event_datetime   timestamptz not null,
	timing           text,
	country_code     text,
	period           text,
	raw              jsonb,
	created_at       timestamptz not null default now(),
	updated_at       timestamptz not null default now(),
	unique (event_type, symbol, event_datetime, event_name)
);

create index if not exists idx_sec_type_dt on stock_economic_calendar (event_type, event_datetime);
create index if not exists idx_sec_symbol on stock_economic_calendar (symbol);
create index if not exists idx_sec_stock_id on stock_economic_calendar (stock_id);

alter table stock_economic_calendar enable row level security;

drop policy if exists "public read stock_economic_calendar" on stock_economic_calendar;
create policy "public read stock_economic_calendar"
	on stock_economic_calendar
	for select
	using (true);
