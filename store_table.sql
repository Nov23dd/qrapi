-- 蝦皮店到店掃描 table（可重複執行，不會刪資料）
create table if not exists public.store_scans (
  id         bigint generated always as identity primary key,
  code       text not null,          -- 寄件編號，例如 TW2670596803248
  time       text,
  created_at timestamptz default now()
);
create unique index if not exists store_scans_code_uidx on public.store_scans (code);

grant usage on schema public to anon, authenticated;
grant select, insert, delete on public.store_scans to anon, authenticated;

alter table public.store_scans enable row level security;
drop policy if exists "store_anon_select" on public.store_scans;
drop policy if exists "store_anon_insert" on public.store_scans;
drop policy if exists "store_anon_delete" on public.store_scans;
create policy "store_anon_select" on public.store_scans for select using (true);
create policy "store_anon_insert" on public.store_scans for insert with check (true);
create policy "store_anon_delete" on public.store_scans for delete using (true);

do $$
begin
  if not exists (select 1 from pg_publication_tables
                 where pubname='supabase_realtime' and schemaname='public' and tablename='store_scans') then
    alter publication supabase_realtime add table public.store_scans;
  end if;
end $$;

notify pgrst, 'reload schema';
