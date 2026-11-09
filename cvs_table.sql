-- 7-11 / 全家寄件掃描 table（可重複執行，不會刪資料，不影響其他表）
create table if not exists public.cvs_scans (
  id         bigint generated always as identity primary key,
  store      text not null check (store in ('711','fm')),   -- 711 = 7-11，fm = 全家
  qr         text not null,          -- QR 原始內容（原樣保留，匯出 PDF 用）
  ref        text not null,          -- 防重複用：7-11 物流條碼 / 全家 QR 第 2 欄
  order_no   text,                   -- 全家：蝦皮訂單編號
  fm_no      text,                   -- 全家：訂單編號
  time       text,
  created_at timestamptz default now()
);
create unique index if not exists cvs_scans_store_ref_uidx on public.cvs_scans (store, ref);

grant usage on schema public to anon, authenticated;
grant select, insert, delete on public.cvs_scans to anon, authenticated;

alter table public.cvs_scans enable row level security;
drop policy if exists "cvs_anon_select" on public.cvs_scans;
drop policy if exists "cvs_anon_insert" on public.cvs_scans;
drop policy if exists "cvs_anon_delete" on public.cvs_scans;
create policy "cvs_anon_select" on public.cvs_scans for select using (true);
create policy "cvs_anon_insert" on public.cvs_scans for insert with check (true);
create policy "cvs_anon_delete" on public.cvs_scans for delete using (true);

do $$
begin
  if not exists (select 1 from pg_publication_tables
                 where pubname='supabase_realtime' and schemaname='public' and tablename='cvs_scans') then
    alter publication supabase_realtime add table public.cvs_scans;
  end if;
end $$;

notify pgrst, 'reload schema';
