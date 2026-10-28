-- Split-trigger dividend + OHLCV rebasis
--
-- stock_dividend.dividend stores split-adjusted amounts (today-basis, not
-- declared) and stock_historical_price stores split-adjusted OHLCV (prices
-- /factor, volume *factor) — both sources (DefeatBeta, yfinance) already
-- deliver this basis. When a new split lands in stock_split, older rows keep
-- the old basis. This migration adds split_adjusted_on (self-stamping,
-- default now() = "amounts include all splits up to fetch time") to both
-- tables and an AFTER INSERT trigger that re-bases rows older than the new
-- split date.
--
-- Idempotency: guard `split_adjusted_on < NEW.date` makes each row divided
-- at most once per split date. Pipeline must NEVER update stock_split
-- (INSERT ... ON CONFLICT DO NOTHING only). build_split_rows sorts events
-- oldest-first so a multi-split batch applies in insertion order.
--
-- Apply manually to Supabase (no local supabase/ dir in this repo).
-- After applying: NOTIFY pgrst, 'reload schema';

alter table stock_dividend
	add column if not exists split_adjusted_on date default now() not null;

-- Backfill: existing rows are today-basis as-of their fetch; stamp with the
-- newest split already in DB (best-effort claim). No splits -> now() = today-basis.
update stock_dividend d
   set split_adjusted_on = coalesce(
         (select max(date) from stock_split s where s.stock_id = d.stock_id),
         now()::date)
 where split_adjusted_on = now()::date;

update stock_historical_price p
   set split_adjusted_on = coalesce(
         (select max(date) from stock_split s where s.stock_id = p.stock_id),
         now()::date)
 where split_adjusted_on = now()::date;

create or replace function public.on_new_split() returns trigger
language plpgsql
as $$
begin
	if NEW.factor is null or NEW.factor = 0 then
		return NEW;
	end if;

	update stock_dividend
	   set dividend = dividend / NEW.factor::float8,
	       split_adjusted_on = NEW.date
	 where stock_id = NEW.stock_id
	   and date < NEW.date
	   and split_adjusted_on < NEW.date;

	update stock_historical_price
	   set open = open / NEW.factor::float8,
	       high = high / NEW.factor::float8,
	       low = low / NEW.factor::float8,
	       close = close / NEW.factor::float8,
	       volume = volume * NEW.factor::float8,
	       split_adjusted_on = NEW.date
	 where stock_id = NEW.stock_id
	   and date < NEW.date
	   and split_adjusted_on < NEW.date;

	return NEW;
end $$;

drop trigger if exists trg_stock_split_recalc on stock_split;

create trigger trg_stock_split_recalc
after insert on stock_split
for each row execute function public.on_new_split();

notify pgrst, 'reload schema';
