-- Author: Sandeep Belgavi. Synthetic PostgreSQL savepoint fixture.
CREATE TEMP TABLE fixture_record (
    id integer PRIMARY KEY,
    label text NOT NULL
);
BEGIN;
INSERT INTO fixture_record VALUES (11, 'accepted-a');
SAVEPOINT optional_record;
INSERT INTO fixture_record VALUES (11, 'duplicate-a'); -- expected error
ROLLBACK TO SAVEPOINT optional_record;
INSERT INTO fixture_record VALUES (12, 'accepted-b');
RELEASE SAVEPOINT optional_record;
SELECT id, label FROM fixture_record ORDER BY id;
ROLLBACK;
SELECT count(*) AS durable_rows FROM fixture_record;
