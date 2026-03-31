-- Farewellify Initial Schema Migration
-- Run this in your NEW Supabase project's SQL Editor

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- TABLE: farewell_events
-- =====================================================
CREATE TABLE farewell_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    honoree_name TEXT NOT NULL,
    honoree_email TEXT,
    organizer_name TEXT NOT NULL,
    organizer_email TEXT NOT NULL,
    deadline TIMESTAMP WITH TIME ZONE NOT NULL,
    message TEXT,
    google_drive_folder_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    access_code TEXT UNIQUE DEFAULT encode(gen_random_bytes(6), 'hex')
);

-- =====================================================
-- TABLE: team_members
-- =====================================================
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES farewell_events(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    invited_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    reminder_sent_at TIMESTAMP WITH TIME ZONE
);

-- =====================================================
-- TABLE: submissions
-- =====================================================
CREATE TABLE submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES farewell_events(id) ON DELETE CASCADE,
    team_member_id UUID REFERENCES team_members(id) ON DELETE CASCADE,
    message TEXT,
    file_url TEXT,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    photo_urls TEXT
);

-- =====================================================
-- INDEXES
-- =====================================================
CREATE INDEX idx_team_members_event_id ON team_members(event_id);
CREATE INDEX idx_submissions_event_id ON submissions(event_id);
CREATE INDEX idx_submissions_team_member_id ON submissions(team_member_id);
CREATE INDEX idx_farewell_events_access_code ON farewell_events(access_code);

-- =====================================================
-- ROW LEVEL SECURITY
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE farewell_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE submissions ENABLE ROW LEVEL SECURITY;

-- Policies for farewell_events
CREATE POLICY "Public can view events with access code" ON farewell_events
    FOR SELECT USING (true);

CREATE POLICY "Public can insert events" ON farewell_events
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Public can update events" ON farewell_events
    FOR UPDATE USING (true);

-- Policies for team_members
CREATE POLICY "Public can view team members" ON team_members
    FOR SELECT USING (true);

CREATE POLICY "Public can insert team members" ON team_members
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Public can update team members" ON team_members
    FOR UPDATE USING (true);

-- Policies for submissions
CREATE POLICY "Public can view submissions" ON submissions
    FOR SELECT USING (true);

CREATE POLICY "Public can insert submissions" ON submissions
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Public can update submissions" ON submissions
    FOR UPDATE USING (true);

-- =====================================================
-- STORAGE BUCKET
-- =====================================================
-- Run this separately in SQL Editor or via Supabase Dashboard:
-- INSERT INTO storage.buckets (id, name, public) VALUES ('uploads', 'uploads', true);
