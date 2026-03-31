-- Farewellify Data Migration
-- Run this AFTER 001_initial_schema.sql in your NEW Supabase project

-- =====================================================
-- FAREWELL EVENTS DATA
-- =====================================================
INSERT INTO farewell_events (id, honoree_name, honoree_email, organizer_name, organizer_email, deadline, message, google_drive_folder_url, created_at, access_code) VALUES
('0edc3a83-fb11-4c39-a47a-dab3de33acc2', 'Julian Arnold', 'julian.arnold@pandata.de', 'Hannah Klenk', 'hannah.klenk@pandata.de', '2026-01-29 11:00:00+00', E'Hi Pandatas,\n\nWe will be celebrating Julian Arnold''s farewell this Thursday and therefore need your help!\n\nFor his farewell card, please send me a few words you''d like to share and any photos you have.\n\nYou can upload handwritten notes or type in a text of your choice.\n\nWe will collect everything on a Miro card, so please send your entry by latest Thursday 11 am.\n\nThanks a lot!\n\nBest,\nHannah', NULL, '2026-01-27 10:17:47.201598+00', '5cf542d396cd'),
('dd1011d2-3185-47a6-81a5-db1a063297a4', 'Julian Arnold', 'julian.arnold@pandata.de', 'Hannah Klenk', 'hannah.klenk@pandata.de', '2026-01-30 11:00:00+00', 'Hi Pandatas! We are celebrating Julian''s farewell and need your help!', NULL, '2026-01-27 11:00:55.321858+00', 'bc75dbf476e4'),
('6fc53bab-a167-4382-b56f-3fe24e827e6d', 'Test Person', 'test.person@pandata.de', 'Test Organizer', 'test.organizer@pandata.de', '2026-01-28 00:00:00+00', E'Hi Pandatas,\n\nWe will be celebrating Test Person''s farewell and therefore need your help!\n\nFor the farewell card, please send a few words you''d like to share and any photos you have.\n\nYou can upload handwritten notes or type in a text of your choice.\n\nPlease submit your entry via this link: [LINK WIRD AUTOMATISCH EINGEFÜGT]\n\nThanks a lot!', NULL, '2026-01-27 13:20:06.630902+00', 'f7df2d79093b'),
('524be2da-766d-4ff8-970a-50e58f04a0cc', 'Julian', 'julian.arnold@pandata.de', 'Hannah', 'hannah.klenk@pandata.de', '2026-01-29 00:00:00+00', E'We''re collecting messages for Julian''s farewell card! \nPlease share a few words and any photos you have. \n\nYou can upload handwritten notes or type a message via our new farewell card app! ', NULL, '2026-01-27 14:18:13.786506+00', '307d75f7b53f');

-- =====================================================
-- TEAM MEMBERS DATA
-- =====================================================
INSERT INTO team_members (id, event_id, name, email, invited_at, reminder_sent_at) VALUES
('9e910214-f021-4e64-881a-e5c81f2f758d', '0edc3a83-fb11-4c39-a47a-dab3de33acc2', 'Adam Butz', 'adam.butz@pandata.de', '2026-01-27 10:17:47.273902+00', NULL),
('fa333132-8b38-40d7-8e28-6d5f121a60b0', '0edc3a83-fb11-4c39-a47a-dab3de33acc2', 'Alexandra Cornea', 'alexandra.cornea@pandata.de', '2026-01-27 10:17:47.338081+00', NULL),
('76e8335c-8948-4c2b-bc82-12b096de09a7', '0edc3a83-fb11-4c39-a47a-dab3de33acc2', 'Aly Nagy', 'aly.nagy@pandata.de', '2026-01-27 10:17:47.401058+00', NULL),
('1a2ae3e5-4642-4948-969d-96672f8c1cea', '0edc3a83-fb11-4c39-a47a-dab3de33acc2', 'Ege Kurşun', 'ege.kursun@pandata.de', '2026-01-27 10:17:47.456224+00', NULL),
('3fcc97cd-37bd-4321-ad81-176d318e2b41', '0edc3a83-fb11-4c39-a47a-dab3de33acc2', 'Emmet Conaty', 'emmet.conaty@pandata.de', '2026-01-27 10:17:47.511608+00', NULL),
('b7a802a4-7739-42b8-aaf6-d6dabbc1d67a', '0edc3a83-fb11-4c39-a47a-dab3de33acc2', 'Federico Bontempi', 'federico.bontempi@pandata.de', '2026-01-27 10:17:47.569885+00', NULL),
('2a670c15-f728-4db9-83ce-70c45798840a', '0edc3a83-fb11-4c39-a47a-dab3de33acc2', 'Fine Stuhr-Wulff', 'fine.stuhr-wulff@pandata.de', '2026-01-27 10:17:47.632701+00', NULL),
('9da2e003-e46e-46fc-a793-7f0d97350588', '0edc3a83-fb11-4c39-a47a-dab3de33acc2', 'Georg Mayer', 'georg.mayer@pandata.de', '2026-01-27 10:17:47.688745+00', NULL),
('a1e963ef-8f66-4869-bc9e-fe4eac1dc87f', '0edc3a83-fb11-4c39-a47a-dab3de33acc2', 'Harry Roper', 'harry.roper@pandata.de', '2026-01-27 10:17:47.753512+00', NULL),
('bc34267f-b5bf-4287-9fe6-8deadfe060eb', '0edc3a83-fb11-4c39-a47a-dab3de33acc2', 'Joana Miranda', 'joana.miranda@pandata.de', '2026-01-27 10:17:47.808034+00', NULL),
('477342dd-5b8a-4844-b42d-123b26af9e15', '0edc3a83-fb11-4c39-a47a-dab3de33acc2', 'Josh Heller', 'josh.heller@pandata.de', '2026-01-27 10:17:47.867394+00', NULL),
('ed72747f-819b-4541-a22b-09767f802f88', '0edc3a83-fb11-4c39-a47a-dab3de33acc2', 'Julius Wagenbach', 'julius.wagenbach@pandata.de', '2026-01-27 10:17:47.925211+00', NULL),
('026f9b63-ba1d-4769-a9cf-c29d01fb7755', '0edc3a83-fb11-4c39-a47a-dab3de33acc2', 'Lorenzo Bernecker', 'lorenzo.bernecker@pandata.de', '2026-01-27 10:17:47.981383+00', NULL),
('ccc943e8-2914-43e0-82a5-40536a748371', '0edc3a83-fb11-4c39-a47a-dab3de33acc2', 'Marco Szeidenleder', 'marco.szeidenleder@pandata.de', '2026-01-27 10:17:48.057078+00', NULL),
('f8379544-2d3b-4c12-b5ca-b4ae2744c8a5', '0edc3a83-fb11-4c39-a47a-dab3de33acc2', 'Nikolai Summers', 'nikolai.summers@pandata.de', '2026-01-27 10:17:48.123191+00', NULL),
('25036be3-aade-49a3-8c9c-67dcff2df30e', '0edc3a83-fb11-4c39-a47a-dab3de33acc2', 'Piotr Wojcik', 'piotr.wojcik@pandata.de', '2026-01-27 10:17:48.185428+00', NULL),
('403726cb-da04-4e99-94d7-c27a20776788', '0edc3a83-fb11-4c39-a47a-dab3de33acc2', 'Polly Jenkinson', 'polly.jenkinson@pandata.de', '2026-01-27 10:17:48.241407+00', NULL),
('6ab8064e-bf79-4c3a-8980-389b2e63c45b', '0edc3a83-fb11-4c39-a47a-dab3de33acc2', 'Riccardo Destratis', 'riccardo.destratis@pandata.de', '2026-01-27 10:17:48.297038+00', NULL),
('37d31b40-59c8-4e5d-bd04-9ec76e7b4dc1', '0edc3a83-fb11-4c39-a47a-dab3de33acc2', 'Valeryia Niamtsova', 'valeryia.niamtsova@pandata.de', '2026-01-27 10:17:48.357142+00', NULL),
('dcfd3480-3a9b-4c72-82c0-f6fcb4a7a486', '0edc3a83-fb11-4c39-a47a-dab3de33acc2', 'Wolfgang Bernecker', 'wolfgang.bernecker@pandata.de', '2026-01-27 10:17:48.411199+00', NULL),
('c2c3fb3e-7fa9-4bcf-b2b9-3727fffb9b36', 'dd1011d2-3185-47a6-81a5-db1a063297a4', 'Adam Butz', 'adam.butz@pandata.de', '2026-01-27 11:00:55.382835+00', NULL),
('a963ee67-4d7a-4698-a6d6-2ff9c3153945', 'dd1011d2-3185-47a6-81a5-db1a063297a4', 'Aly Nagy', 'aly.nagy@pandata.de', '2026-01-27 11:00:55.454621+00', NULL),
('253d1c84-a4b7-4a24-8724-76bde428cf43', '524be2da-766d-4ff8-970a-50e58f04a0cc', 'Valeryia Niamtsova', 'valeryia.niamtsova@pandata.de', '2026-01-27 14:19:09.651384+00', NULL),
('f32373ff-9a25-4080-82b2-b5a002537f19', '524be2da-766d-4ff8-970a-50e58f04a0cc', 'Wolfgang Bernecker', 'wolfgang.bernecker@pandata.de', '2026-01-27 14:19:10.207645+00', NULL),
('e64a697e-cd76-47d7-8cd9-2319c2665988', '6fc53bab-a167-4382-b56f-3fe24e827e6d', 'Hannah Klenk', 'hannah.klenk@pandata.de', '2026-01-27 14:01:30.59167+00', NULL),
('d8dd88dc-dab7-4ac1-b6f7-f532ce4f81ba', '524be2da-766d-4ff8-970a-50e58f04a0cc', 'Adam Butz', 'adam.butz@pandata.de', '2026-01-27 14:18:55.101492+00', NULL),
('f8157a74-3865-4532-9472-5e2b22b6a475', '524be2da-766d-4ff8-970a-50e58f04a0cc', 'Alexandra Cornea', 'alexandra.cornea@pandata.de', '2026-01-27 14:18:55.805108+00', NULL),
('416f8e2c-0ff8-4e5c-9be8-2ddab5981771', '524be2da-766d-4ff8-970a-50e58f04a0cc', 'Aly Nagy', 'aly.nagy@pandata.de', '2026-01-27 14:18:56.277864+00', NULL),
('c0ac39de-eb4d-4a2f-a88d-e6ab76c51ecc', '524be2da-766d-4ff8-970a-50e58f04a0cc', 'Ege Kurşun', 'ege.kursun@pandata.de', '2026-01-27 14:18:57.035615+00', NULL),
('10389071-fcd9-41e0-b109-d300af73531a', '524be2da-766d-4ff8-970a-50e58f04a0cc', 'Emmet Conaty', 'emmet.conaty@pandata.de', '2026-01-27 14:19:01.548259+00', NULL),
('fba9e4c5-c1c1-49a5-bf5c-3334b292954e', '524be2da-766d-4ff8-970a-50e58f04a0cc', 'Federico Bontempi', 'federico.bontempi@pandata.de', '2026-01-27 14:19:02.27009+00', NULL),
('941e0921-0576-4dcf-93d8-2c095fc0b48f', '524be2da-766d-4ff8-970a-50e58f04a0cc', 'Fine Stuhr-Wulff', 'fine.stuhr-wulff@pandata.de', '2026-01-27 14:19:02.778404+00', NULL),
('793dcb5d-379c-43b3-8558-c408e7544164', '524be2da-766d-4ff8-970a-50e58f04a0cc', 'Georg Mayer', 'georg.mayer@pandata.de', '2026-01-27 14:19:03.298645+00', NULL),
('220a0082-646e-4c81-a872-1655f1d4a909', '524be2da-766d-4ff8-970a-50e58f04a0cc', 'Hannah Klenk', 'hannah.klenk@pandata.de', '2026-01-27 14:19:03.702993+00', NULL),
('ea29f9b0-d1b3-4de1-b358-f2ef9a35027b', '524be2da-766d-4ff8-970a-50e58f04a0cc', 'Harry Roper', 'harry.roper@pandata.de', '2026-01-27 14:19:04.497273+00', NULL),
('83bceb41-ad68-4dfc-9580-4354182bdf52', '524be2da-766d-4ff8-970a-50e58f04a0cc', 'Joana Miranda', 'joana.miranda@pandata.de', '2026-01-27 14:19:04.960318+00', NULL),
('404fd4d4-5bcd-4bbe-b5ba-b082c7a426f5', '524be2da-766d-4ff8-970a-50e58f04a0cc', 'Josh Heller', 'josh.heller@pandata.de', '2026-01-27 14:19:05.630985+00', NULL),
('c697f015-f8f1-463e-88e8-d39496c1260e', '524be2da-766d-4ff8-970a-50e58f04a0cc', 'Julius Wagenbach', 'julius.wagenbach@pandata.de', '2026-01-27 14:19:06.29735+00', NULL),
('73463a2f-791d-4135-93e4-4d5e9c4df8a5', '524be2da-766d-4ff8-970a-50e58f04a0cc', 'Lorenzo Bernecker', 'lorenzo.bernecker@pandata.de', '2026-01-27 14:19:06.873039+00', NULL),
('12ed646a-d187-4de4-b807-8b87d903d625', '524be2da-766d-4ff8-970a-50e58f04a0cc', 'Marco Szeidenleder', 'marco.szeidenleder@pandata.de', '2026-01-27 14:19:07.267966+00', NULL),
('d9678512-75a8-4c9b-b000-6de4f390edd3', '524be2da-766d-4ff8-970a-50e58f04a0cc', 'Nikolai Summers', 'nikolai.summers@pandata.de', '2026-01-27 14:19:07.742172+00', NULL),
('b83fb222-ddbe-4dda-9afe-393d9163279c', '524be2da-766d-4ff8-970a-50e58f04a0cc', 'Piotr Wojcik', 'piotr.wojcik@pandata.de', '2026-01-27 14:19:08.218458+00', NULL),
('d8a25f5a-a8c5-4c52-8673-5a3a3f63118a', '524be2da-766d-4ff8-970a-50e58f04a0cc', 'Polly Jenkinson', 'polly.jenkinson@pandata.de', '2026-01-27 14:19:08.684731+00', NULL),
('c23313be-351e-4cde-9b0b-abad9be47aaa', '524be2da-766d-4ff8-970a-50e58f04a0cc', 'Riccardo Destratis', 'riccardo.destratis@pandata.de', '2026-01-27 14:19:09.17057+00', NULL);

-- =====================================================
-- SUBMISSIONS DATA
-- =====================================================
INSERT INTO submissions (id, event_id, team_member_id, message, file_url, submitted_at, photo_urls) VALUES
('b3be4b12-6b40-49eb-8736-306416cf87dc', 'dd1011d2-3185-47a6-81a5-db1a063297a4', 'c2c3fb3e-7fa9-4bcf-b2b9-3727fffb9b36', 'Alles Gute Julian!', NULL, '2026-01-27 11:17:59.394218+00', NULL),
('f6872cc9-de7c-4f7c-b611-ea7aeb4f8975', '6fc53bab-a167-4382-b56f-3fe24e827e6d', 'e64a697e-cd76-47d7-8cd9-2319c2665988', NULL, '/uploads/6fc53bab-a167-4382-b56f-3fe24e827e6d_4c5d371b.jpg', '2026-01-27 13:27:45.316406+00', NULL),
('3724156b-0684-4d0c-b2b8-6ee17596be25', '524be2da-766d-4ff8-970a-50e58f04a0cc', '416f8e2c-0ff8-4e5c-9be8-2ddab5981771', E'Julian, \r\n\r\nPandata will lose a gem, it has been great getting to know and to work with you, we joined at around the same time and we had one hell of a journey, thanks for being a part of it for me. \r\n\r\nWishing you nothing but success, fulfillment, and great adventures in whatever comes next. You''ll be missed. \r\n\r\nCheers \r\nAly', NULL, '2026-01-27 15:20:47.829866+00', NULL),
('039cff5c-5148-41f5-85da-2af2770a6afa', '524be2da-766d-4ff8-970a-50e58f04a0cc', '793dcb5d-379c-43b3-8558-c408e7544164', E'Viel Spaß und Erfolg bei Trade Republic! Wird sicher ne coole neue Erfahrung und auf ein paar weitere Mittagessen. \r\n', NULL, '2026-01-27 16:52:20.632412+00', NULL);

-- NOTE: The submission with photos (d09d219a-d944-4fa1-9a05-92932b4efd29) references 
-- files stored in the OLD Supabase bucket. You'll need to:
-- 1. Download those files from the old project
-- 2. Upload them to the new project's storage bucket
-- 3. Update the URLs in this submission
-- For now, we'll insert it with the old URLs (which won't work until migrated):
INSERT INTO submissions (id, event_id, team_member_id, message, file_url, submitted_at, photo_urls) VALUES
('d09d219a-d944-4fa1-9a05-92932b4efd29', '524be2da-766d-4ff8-970a-50e58f04a0cc', '220a0082-646e-4c81-a872-1655f1d4a909', NULL, 'https://datpxrveaizpigltowju.supabase.co/storage/v1/object/public/uploads/524be2da-766d-4ff8-970a-50e58f04a0cc_msg_cb0ea2f1.jpg', '2026-01-27 15:19:35.802603+00', '["https://datpxrveaizpigltowju.supabase.co/storage/v1/object/public/uploads/524be2da-766d-4ff8-970a-50e58f04a0cc_photo_81b100a3.jpg", "https://datpxrveaizpigltowju.supabase.co/storage/v1/object/public/uploads/524be2da-766d-4ff8-970a-50e58f04a0cc_photo_e2745453.jpg", "https://datpxrveaizpigltowju.supabase.co/storage/v1/object/public/uploads/524be2da-766d-4ff8-970a-50e58f04a0cc_photo_0035e579.jpg", "https://datpxrveaizpigltowju.supabase.co/storage/v1/object/public/uploads/524be2da-766d-4ff8-970a-50e58f04a0cc_photo_a43d663c.jpg", "https://datpxrveaizpigltowju.supabase.co/storage/v1/object/public/uploads/524be2da-766d-4ff8-970a-50e58f04a0cc_photo_a449d9fe.jpg", "https://datpxrveaizpigltowju.supabase.co/storage/v1/object/public/uploads/524be2da-766d-4ff8-970a-50e58f04a0cc_photo_83676cb0.jpg", "https://datpxrveaizpigltowju.supabase.co/storage/v1/object/public/uploads/524be2da-766d-4ff8-970a-50e58f04a0cc_photo_2cb15f7e.jpg", "https://datpxrveaizpigltowju.supabase.co/storage/v1/object/public/uploads/524be2da-766d-4ff8-970a-50e58f04a0cc_photo_1260b971.jpg", "https://datpxrveaizpigltowju.supabase.co/storage/v1/object/public/uploads/524be2da-766d-4ff8-970a-50e58f04a0cc_photo_be0d9bd3.jpg", "https://datpxrveaizpigltowju.supabase.co/storage/v1/object/public/uploads/524be2da-766d-4ff8-970a-50e58f04a0cc_photo_896366fa.jpg"]');
