"""Author: Sandeep Belgavi. Run original SQL fixture through psycopg, no model."""
from pathlib import Path
import os,json,psycopg
with psycopg.connect(os.environ['DATABASE_URL'],autocommit=True) as connection:
    version=connection.execute('SHOW server_version').fetchone()[0]
    cur=connection.execute((Path(__file__).parent/'example.sql').read_text(encoding='utf-8'),prepare=False)
    outputs=[]
    while True:
        if cur.description:outputs.append(cur.fetchall())
        if not cur.nextset():break
    assert any('PASS:' in str(rows) for rows in outputs)
    print(json.dumps({'server_version':version,'results':outputs}))
