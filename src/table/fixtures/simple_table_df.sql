--
-- PostgreSQL database dump
--

-- Dumped from database version 9.6.3
-- Dumped by pg_dump version 9.6.3

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: __ONTASK_WORKFLOW_TABLE_1; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "__ONTASK_WORKFLOW_TABLE_1" (
    age double precision,
    email text,
    sid bigint,
    another text,
    name text,
    one text,
    registered boolean,
    "when" timestamp without time zone
);


--
-- Data for Name: __ONTASK_WORKFLOW_TABLE_1; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "__ONTASK_WORKFLOW_TABLE_1" (age, email, sid, another, name, one, registered, "when") FROM stdin;
12	student1@bogus.com	1	bbb	Carmelo Coton	aaa	t	2017-10-11 00:33:44
12.0999999999999996	student2@bogus.com	2	aaa	Carmelo Coton	bbb	f	2017-10-11 00:32:44
13.1999999999999993	student3@bogus.com	3	bbb	Carmelo Coton2	aaa	t	2017-10-11 00:32:44
\.


--
-- PostgreSQL database dump complete
--

