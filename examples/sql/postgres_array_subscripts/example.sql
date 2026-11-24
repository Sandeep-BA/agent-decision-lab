-- Author: Sandeep Belgavi. Synthetic original array-coordinate assertions.
-- Run in a disposable database; this transaction leaves no tables behind.
BEGIN;
CREATE TEMP TABLE vector_fixture(a integer[]);
INSERT INTO vector_fixture VALUES ('[0:2]={10,NULL,30}');
DO $$ DECLARE a integer[]; got integer[]; BEGIN
 SELECT v.a INTO a FROM vector_fixture v;
 IF array_lower(a,1)<>0 OR array_upper(a,1)<>2 OR cardinality(a)<>3 THEN RAISE EXCEPTION 'shape mismatch'; END IF;
 IF a[0]<>10 OR a[1] IS NOT NULL OR a[2]<>30 THEN RAISE EXCEPTION 'subscript values wrong'; END IF;
 SELECT array_agg(a[s] ORDER BY s) INTO got FROM generate_subscripts(a,1) AS s;
 IF got IS DISTINCT FROM ARRAY[10,NULL,30] THEN RAISE EXCEPTION 'subscript enumeration wrong'; END IF;
 SELECT array_agg(a[ordinal] ORDER BY ordinal) INTO got FROM unnest(a) WITH ORDINALITY AS u(value,ordinal);
 IF got IS DISTINCT FROM ARRAY[NULL,30,NULL]::integer[] THEN RAISE EXCEPTION 'ordinal mismatch fixture changed'; END IF;
 IF cardinality(ARRAY[]::integer[])<>0 OR array_length(ARRAY[]::integer[],1) IS NOT NULL THEN RAISE EXCEPTION 'empty semantics wrong'; END IF;
 IF cardinality(NULL::integer[]) IS NOT NULL THEN RAISE EXCEPTION 'null semantics wrong'; END IF;
 IF '[0:1]={10,20}'::integer[]=ARRAY[10,20] THEN RAISE EXCEPTION 'shape equality fixture wrong'; END IF;
 IF array_lower('[-2:0]={5,6,7}'::integer[],1)<>-2 THEN RAISE EXCEPTION 'negative lower bound lost'; END IF;
END $$;
CREATE TEMP TABLE list_contract(samples integer[] NOT NULL CHECK(cardinality(samples)=0 OR (array_ndims(samples)=1 AND array_lower(samples,1)=1)));
INSERT INTO list_contract VALUES (ARRAY[10,NULL,30]),(ARRAY[]::integer[]);
DO $$ BEGIN
 BEGIN
  INSERT INTO list_contract VALUES ('[0:2]={10,NULL,30}');
  RAISE EXCEPTION 'zero-based list accepted';
 EXCEPTION WHEN check_violation THEN NULL;
 END;
 BEGIN
  INSERT INTO list_contract VALUES (ARRAY[[1,2],[3,4]]);
  RAISE EXCEPTION 'multidimensional list accepted';
 EXCEPTION WHEN check_violation THEN NULL;
 END;
 BEGIN
  INSERT INTO list_contract VALUES (NULL);
  RAISE EXCEPTION 'null list accepted';
 EXCEPTION WHEN not_null_violation THEN NULL;
 END;
END $$;
SELECT s AS original_subscript,a[s] AS value FROM vector_fixture CROSS JOIN LATERAL generate_subscripts(a,1) s ORDER BY s;
SELECT 'PASS: array shape, subscript mapping, ordinal mismatch, empty/null, equality, negative bounds, shape constraints' AS result;
ROLLBACK;
