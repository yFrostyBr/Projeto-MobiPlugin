-- Create tables for Supabase
create table if not exists assets (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  type text not null,
  version text default '1.0',
  json_spec jsonb,
  skp_url text,
  skp_base64 text,
  default_params jsonb,
  tags text[] default '{}',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists materials (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  color text,
  texture_url text,
  metadata jsonb,
  created_at timestamptz default now()
);

create table if not exists asset_materials (
  asset_id uuid references assets(id) on delete cascade,
  material_id uuid references materials(id) on delete cascade,
  role text,
  primary key (asset_id, material_id)
);

-- Enable Row Level Security (RLS)
alter table assets enable row level security;
alter table materials enable row level security;
alter table asset_materials enable row level security;

-- Create policies (allow read for authenticated users, write for service role)
create policy "Assets are viewable by authenticated users" on assets
  for select using (auth.role() = 'authenticated' or auth.role() = 'anon');

create policy "Assets are insertable by authenticated users" on assets
  for insert with check (auth.role() = 'authenticated' or auth.role() = 'service_role');

create policy "Assets are updatable by authenticated users" on assets
  for update using (auth.role() = 'authenticated' or auth.role() = 'service_role');

create policy "Assets are deletable by authenticated users" on assets
  for delete using (auth.role() = 'authenticated' or auth.role() = 'service_role');

-- Similar policies for materials
create policy "Materials are viewable by authenticated users" on materials
  for select using (auth.role() = 'authenticated' or auth.role() = 'anon');

create policy "Materials are insertable by authenticated users" on materials
  for insert with check (auth.role() = 'authenticated' or auth.role() = 'service_role');

-- Asset materials policies
create policy "Asset materials are viewable by authenticated users" on asset_materials
  for select using (auth.role() = 'authenticated' or auth.role() = 'anon');

create policy "Asset materials are insertable by authenticated users" on asset_materials
  for insert with check (auth.role() = 'authenticated' or auth.role() = 'service_role');

-- Create storage bucket for SKP files (execute this in Supabase dashboard -> Storage)
-- insert into storage.buckets (id, name, public) values ('skp-files', 'skp-files', true);

-- Storage policies
-- create policy "SKP files are publicly accessible" on storage.objects
--   for select using (bucket_id = 'skp-files');

-- create policy "Users can upload SKP files" on storage.objects
--   for insert with check (bucket_id = 'skp-files' and (auth.role() = 'authenticated' or auth.role() = 'service_role'));

-- Insert some sample data
insert into assets (name, type, version, skp_url, default_params, tags) values
  ('puxador_standard', 'hardware', '1.0', 'https://pcaqqbooticnykbxtfjm.supabase.co/storage/v1/object/public/skp-files/puxador_standard.skp', '{"width": 120, "height": 30}', '{"handle", "metal", "standard"}'),
  ('corredicá_lateral', 'hardware', '1.0', 'https://pcaqqbooticnykbxtfjm.supabase.co/storage/v1/object/public/skp-files/corredica_lateral.skp', '{"length": 450, "load_capacity": "45kg"}', '{"runner", "slide", "hardware"}'),
  ('painel_mdf', 'component', '1.0', null, '{"thickness": 18, "material": "MDF"}', '{"panel", "mdf", "wood"}'),
  ('balcao_simples', 'furniture', '1.0', 'https://pcaqqbooticnykbxtfjm.supabase.co/storage/v1/object/public/skp-files/balcao_simples.skp', '{"width": 1200, "height": 900, "depth": 600}', '{"furniture", "balcao", "cabinet"}')
on conflict do nothing;

insert into materials (name, color, metadata) values
  ('MDF', '#D2B48C', '{"type": "wood", "density": "medium"}'),
  ('Metal', '#C0C0C0', '{"type": "metal", "finish": "brushed"}'),
  ('Steel', '#708090', '{"type": "metal", "strength": "high"}'),
  ('Compensado', '#DEB887', '{"type": "wood", "layers": "multiple"}')
on conflict do nothing;