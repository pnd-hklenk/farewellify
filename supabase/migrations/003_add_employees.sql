-- Add employees table (missing from initial migration)
-- Run this in your Supabase project's SQL Editor

CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- RLS
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all" ON employees FOR ALL USING (true);

-- Seed with Pandata team
INSERT INTO employees (name, email, is_active) VALUES
('Adam Butz', 'adam.butz@pandata.de', true),
('Alexandra Cornea', 'alexandra.cornea@pandata.de', true),
('Aly Nagy', 'aly.nagy@pandata.de', true),
('Ege Kurşun', 'ege.kursun@pandata.de', true),
('Emmet Conaty', 'emmet.conaty@pandata.de', true),
('Federico Bontempi', 'federico.bontempi@pandata.de', true),
('Fine Stuhr-Wulff', 'fine.stuhr-wulff@pandata.de', true),
('Georg Mayer', 'georg.mayer@pandata.de', true),
('Hannah Klenk', 'hannah.klenk@pandata.de', true),
('Harry Roper', 'harry.roper@pandata.de', true),
('Joana Miranda', 'joana.miranda@pandata.de', true),
('Josh Heller', 'josh.heller@pandata.de', true),
('Julian Arnold', 'julian.arnold@pandata.de', true),
('Julius Wagenbach', 'julius.wagenbach@pandata.de', true),
('Krisztina Papp', 'krisztina.papp@pandata.de', false),
('Lorenzo Bernecker', 'lorenzo.bernecker@pandata.de', true),
('Marco Szeidenleder', 'marco.szeidenleder@pandata.de', true),
('Nikolai Summers', 'nikolai.summers@pandata.de', true),
('Piotr Wojcik', 'piotr.wojcik@pandata.de', true),
('Polly Jenkinson', 'polly.jenkinson@pandata.de', true),
('Riccardo Destratis', 'riccardo.destratis@pandata.de', true),
('Valeryia Niamtsova', 'valeryia.niamtsova@pandata.de', true),
('Wolfgang Bernecker', 'wolfgang.bernecker@pandata.de', true)
ON CONFLICT (email) DO NOTHING;
