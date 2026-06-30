-- ============================================================
-- 蝦皮環保包裹掃描 table  完整建置腳本（可重複執行）
-- ============================================================

-- 1) 建表（已存在就跳過，不會刪資料）
create table if not exists public.shopee_scans (
  id         bigint generated always as identity primary key,
  qr         text not null,          -- QR 完整內容，例如 2_2149736_SPTO20260625LWBLF
  order_no   text,                   -- 拆出的訂單號，例如 2149736
  spto       text,                   -- 拆出的 SPTO 單號，例如 SPTO20260625LWBLF
  time       text,                   -- 顯示用時間字串
  created_at timestamptz default now()
);

-- 2) 防同一個 QR 重複寫入
create unique index if not exists shopee_scans_qr_uidx on public.shopee_scans (qr);

-- 3) ★ 關鍵：授權給 API 角色（anon/authenticated），否則表不會出現在 API schema 快取
grant usage on schema public to anon, authenticated;
grant select, insert, update, delete on public.shopee_scans to anon, authenticated;

-- 4) RLS：開啟並允許用 publishable/anon key 讀寫（和現有 scans 表一致）
alter table public.shopee_scans enable row level security;

drop policy if exists "shopee_anon_select" on public.shopee_scans;
drop policy if exists "shopee_anon_insert" on public.shopee_scans;
drop policy if exists "shopee_anon_delete" on public.shopee_scans;

create policy "shopee_anon_select" on public.shopee_scans for select using (true);
create policy "shopee_anon_insert" on public.shopee_scans for insert with check (true);
create policy "shopee_anon_delete" on public.shopee_scans for delete using (true);

-- 5) 即時同步（先檢查，避免「already member」錯誤）
do $$
begin
  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime'
      and schemaname = 'public'
      and tablename = 'shopee_scans'
  ) then
    alter publication supabase_realtime add table public.shopee_scans;
  end if;
end $$;

-- 6) 強制 PostgREST 重新載入 schema 快取
notify pgrst, 'reload schema';
