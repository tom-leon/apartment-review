--
-- PostgreSQL database dump
--

\restrict seed

-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: apartment; Type: TABLE DATA; Schema: public; Owner: tom
--

INSERT INTO public.apartment (uid, osm_type, osm_id, osm_class, street, house_number, city, state, postcode, country, country_code, display_name, created_at, updated_at) VALUES ('5ee804e1-a8fe-48fd-9fb2-22e204fb36ec', NULL, NULL, NULL, 'Sample Street', '12', 'Melbourne', 'Victoria', '3065', 'Australia', 'AU', '12, Sample Street, Fitzroy, Melbourne, Victoria, 3065, Australia', '2026-11-19 11:23:47.062228', '2026-11-19 11:23:47.062232');
INSERT INTO public.apartment (uid, osm_type, osm_id, osm_class, street, house_number, city, state, postcode, country, country_code, display_name, created_at, updated_at) VALUES ('f4541be4-3c7a-490f-8ac1-4d4cee9f9a2c', NULL, NULL, NULL, 'Example Road', '88', 'Sydney', 'New South Wales', '2037', 'Australia', 'AU', '88, Example Road, Glebe, Sydney, New South Wales, 2037, Australia', '2026-11-19 11:23:47.062327', '2026-11-19 11:23:47.062331');
INSERT INTO public.apartment (uid, osm_type, osm_id, osm_class, street, house_number, city, state, postcode, country, country_code, display_name, created_at, updated_at) VALUES ('c0aeb431-3ec3-44f0-ad44-2f5508f2bfc9', NULL, NULL, NULL, 'Demo Avenue', '15', 'Brisbane', 'Queensland', '4101', 'Australia', 'AU', '15, Demo Avenue, West End, Brisbane, Queensland, 4101, Australia', '2026-11-19 11:23:47.062379', '2026-11-19 11:23:47.062383');
INSERT INTO public.apartment (uid, osm_type, osm_id, osm_class, street, house_number, city, state, postcode, country, country_code, display_name, created_at, updated_at) VALUES ('54b244d9-f217-46e8-adb4-589eccf7a0a5', NULL, NULL, NULL, 'Placeholder Parade', '7', 'Adelaide', 'South Australia', '5000', 'Australia', 'AU', '7, Placeholder Parade, Adelaide, Adelaide, South Australia, 5000, Australia', '2026-11-19 11:23:47.062433', '2026-11-19 11:23:47.062437');
INSERT INTO public.apartment (uid, osm_type, osm_id, osm_class, street, house_number, city, state, postcode, country, country_code, display_name, created_at, updated_at) VALUES ('1085b76e-fd87-4bac-b6ca-c4a47f6ea988', NULL, NULL, NULL, 'Mock Lane', '301', 'Perth', 'Western Australia', '6000', 'Australia', 'AU', '301, Mock Lane, Perth, Perth, Western Australia, 6000, Australia', '2026-11-19 11:23:47.062482', '2026-11-19 11:23:47.062485');
INSERT INTO public.apartment (uid, osm_type, osm_id, osm_class, street, house_number, city, state, postcode, country, country_code, display_name, created_at, updated_at) VALUES ('189d3a73-c894-4e4e-975c-15d3a301d5f4', NULL, NULL, NULL, 'Testing Terrace', '9', 'Hobart', 'Tasmania', '7000', 'Australia', 'AU', '9, Testing Terrace, Hobart, Hobart, Tasmania, 7000, Australia', '2026-11-19 11:23:47.06253', '2026-11-19 11:23:47.062534');


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: tom
--

INSERT INTO public."user" (uid, name, email, google_sub, is_active, created_at, updated_at) VALUES ('ef0c5c1a-2b4f-4890-bb8a-d01d1628f2bb', 'Sample Reviewer 1', 'sample.reviewer1@example.com', 'seed-1', true, '2026-11-19 11:23:47.061963', '2026-11-19 11:23:47.061969');
INSERT INTO public."user" (uid, name, email, google_sub, is_active, created_at, updated_at) VALUES ('c349dd74-92e3-464d-b830-15795928a5ee', 'Sample Reviewer 2', 'sample.reviewer2@example.com', 'seed-2', true, '2026-11-19 11:23:47.062057', '2026-11-19 11:23:47.062061');
INSERT INTO public."user" (uid, name, email, google_sub, is_active, created_at, updated_at) VALUES ('360b5500-0de7-4807-9ae4-13e7ed8b264f', 'Sample Reviewer 3', 'sample.reviewer3@example.com', 'seed-3', true, '2026-11-19 11:23:47.062102', '2026-11-19 11:23:47.062105');
INSERT INTO public."user" (uid, name, email, google_sub, is_active, created_at, updated_at) VALUES ('c62e5b4b-93ae-4699-9367-683995dd7a17', 'Sample Reviewer 4', 'sample.reviewer4@example.com', 'seed-4', true, '2026-11-19 11:23:47.062143', '2026-11-19 11:23:47.062147');
INSERT INTO public."user" (uid, name, email, google_sub, is_active, created_at, updated_at) VALUES ('fb39c338-354f-4650-82df-3d2d8ea3317e', 'Sample Reviewer 5', 'sample.reviewer5@example.com', 'seed-5', true, '2026-11-19 11:23:47.062181', '2026-11-19 11:23:47.062185');


--
-- Data for Name: review; Type: TABLE DATA; Schema: public; Owner: tom
--

INSERT INTO public.review (uid, apartment_uid, user_uid, title, content, landlord_rating, location_rating, condition_rating, quietness_rating, status, created_at, updated_at) VALUES ('d1adaa89-74f8-4b9f-80a8-a08d626b5ab3', '5ee804e1-a8fe-48fd-9fb2-22e204fb36ec', 'ef0c5c1a-2b4f-4890-bb8a-d01d1628f2bb', NULL, 'Trams run past the bedroom window until 1am. Pick a unit at the back.', 60, 95, 70, 35, 'published', '2026-08-02 00:00:00', '2026-11-19 11:23:47.06259');
INSERT INTO public.review (uid, apartment_uid, user_uid, title, content, landlord_rating, location_rating, condition_rating, quietness_rating, status, created_at, updated_at) VALUES ('c902f1cf-b5d3-482c-9f12-51be17525a39', '5ee804e1-a8fe-48fd-9fb2-22e204fb36ec', 'c349dd74-92e3-464d-b830-15795928a5ee', NULL, 'Solid old building with thick walls. A leaking tap was fixed within the week.', 70, 90, 80, 60, 'published', '2026-09-14 00:00:00', '2026-11-19 11:23:47.062673');
INSERT INTO public.review (uid, apartment_uid, user_uid, title, content, landlord_rating, location_rating, condition_rating, quietness_rating, status, created_at, updated_at) VALUES ('d3535c64-82c6-48bd-b67e-c01e5e520323', '5ee804e1-a8fe-48fd-9fb2-22e204fb36ec', '360b5500-0de7-4807-9ae4-13e7ed8b264f', NULL, 'Great light and a short walk to everything, but repairs took six weeks.', 55, 95, 75, 79, 'published', '2026-11-10 00:00:00', '2026-11-19 11:23:47.062715');
INSERT INTO public.review (uid, apartment_uid, user_uid, title, content, landlord_rating, location_rating, condition_rating, quietness_rating, status, created_at, updated_at) VALUES ('86a8af51-3202-41a4-82e4-ebeb4c7e5f64', 'f4541be4-3c7a-490f-8ac1-4d4cee9f9a2c', 'ef0c5c1a-2b4f-4890-bb8a-d01d1628f2bb', NULL, 'Quiet street, five minutes to the light rail, and every email was answered within a day. The one real problem is damp in the back bedroom each winter, which gets painted over instead of fixed. Ask to see that room with the wardrobe pulled away from the wall before you sign anything.', 88, 92, 70, 90, 'published', '2026-11-08 00:00:00', '2026-11-19 11:23:47.062761');
INSERT INTO public.review (uid, apartment_uid, user_uid, title, content, landlord_rating, location_rating, condition_rating, quietness_rating, status, created_at, updated_at) VALUES ('f882ae7c-7af4-4ca6-b946-420378446397', 'c0aeb431-3ec3-44f0-ad44-2f5508f2bfc9', 'c349dd74-92e3-464d-b830-15795928a5ee', NULL, 'The bar downstairs plays music until 3am on weekends.', 50, 80, 40, 10, 'published', '2026-10-01 00:00:00', '2026-11-19 11:23:47.062803');
INSERT INTO public.review (uid, apartment_uid, user_uid, title, content, landlord_rating, location_rating, condition_rating, quietness_rating, status, created_at, updated_at) VALUES ('e595ad13-98ee-46ae-b04f-bc3c60b6d420', 'c0aeb431-3ec3-44f0-ad44-2f5508f2bfc9', 'c62e5b4b-93ae-4699-9367-683995dd7a17', NULL, 'Cockroaches in the kitchen, and the lift was out for a month.', 20, 75, 30, 23, 'published', '2026-11-05 00:00:00', '2026-11-19 11:23:47.062843');
INSERT INTO public.review (uid, apartment_uid, user_uid, title, content, landlord_rating, location_rating, condition_rating, quietness_rating, status, created_at, updated_at) VALUES ('50523a32-f769-4e62-b81a-05d3312548c3', '54b244d9-f217-46e8-adb4-589eccf7a0a5', 'fb39c338-354f-4650-82df-3d2d8ea3317e', NULL, 'Bond came back in full within a week. No dramas.', NULL, NULL, NULL, NULL, 'published', '2026-11-01 00:00:00', '2026-11-19 11:23:47.062884');
INSERT INTO public.review (uid, apartment_uid, user_uid, title, content, landlord_rating, location_rating, condition_rating, quietness_rating, status, created_at, updated_at) VALUES ('0ccc44fe-9714-4d6d-b513-57905fdb363e', '1085b76e-fd87-4bac-b6ca-c4a47f6ea988', '360b5500-0de7-4807-9ae4-13e7ed8b264f', NULL, 'Quiet, clean, and the heating actually works.', 90, 85, 88, 80, 'published', '2026-06-01 00:00:00', '2026-11-19 11:23:47.062935');
INSERT INTO public.review (uid, apartment_uid, user_uid, title, content, landlord_rating, location_rating, condition_rating, quietness_rating, status, created_at, updated_at) VALUES ('a7e58afe-7bc7-477f-a9d8-4d2b47cd8399', '1085b76e-fd87-4bac-b6ca-c4a47f6ea988', 'c62e5b4b-93ae-4699-9367-683995dd7a17', NULL, 'Fair rent for the area. Parking is a fight after 6pm.', 75, 85, 80, 70, 'published', '2026-07-20 00:00:00', '2026-11-19 11:23:47.062975');
INSERT INTO public.review (uid, apartment_uid, user_uid, title, content, landlord_rating, location_rating, condition_rating, quietness_rating, status, created_at, updated_at) VALUES ('49ac122f-cc29-479e-bb79-eb4f2ca92808', '189d3a73-c894-4e4e-975c-15d3a301d5f4', 'fb39c338-354f-4650-82df-3d2d8ea3317e', NULL, 'Mould on the bathroom ceiling came back after every repaint.', 30, 60, 20, 50, 'pending', '2026-11-15 00:00:00', '2026-11-19 11:23:47.063017');


--
-- PostgreSQL database dump complete
--

\unrestrict seed

