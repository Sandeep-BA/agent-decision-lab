-- Author: Sandeep Belgavi. Run only in a disposable database. Belgavi's Book Store is fictional.
CREATE TABLE book_order (id bigint PRIMARY KEY);
CREATE TABLE order_line (
    id bigint PRIMARY KEY,
    order_id bigint NOT NULL REFERENCES book_order(id),
    payload text NOT NULL
);
INSERT INTO book_order VALUES (1), (2);
INSERT INTO order_line
SELECT n, 1, 'synthetic-' || n
FROM generate_series(1, 100000) AS n;
ANALYZE book_order;
ANALYZE order_line;

-- Without a child index: repeat this and capture the full plan.
BEGIN;
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
DELETE FROM book_order WHERE id = 2;
ROLLBACK;

CREATE INDEX order_line_order_idx ON order_line(order_id);
ANALYZE order_line;

-- With the child index: compare the trigger time and buffers.
BEGIN;
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
DELETE FROM book_order WHERE id = 2;
ROLLBACK;
