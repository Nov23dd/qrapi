-- 蝦皮環保包裹掃描 table
create table if not exists public.shopee_scans (
  id         bigint generated always as identity primary key,
  qr         text not null,          -- QR 完整內容，例如 2_2149736_SPTO20260625LWBLF
  order_no   text,                   -- 拆出的訂單號，例如 2149736
  spto       text,                   -- 拆出的 SPTO 單號，例如 SPTO20260625LWBLF
  time       text,                   -- 顯示用時間字串
  created_at timestamptz default now()
);

-- 防同一個 QR 重複寫入（資料庫層級保險，前端也有擋）
create unique index if not exists shopee_scans_qr_uidx on public.shopee_scans (qr);

-- 開啟即時同步（多台裝置畫面同步更新）
alter publication supabase_realtime add table public.shopee_scans;

-- RLS：用 publishable/anon key 可讀寫（和現有 scans 表一致）
alter table public.shopee_scans enable row level security;

create policy "shopee_anon_select" on public.shopee_scans for select using (true);
create policy "shopee_anon_insert" on public.shopee_scans for insert with check (true);
create policy "shopee_anon_delete" on public.shopee_scans for delete using (true);
