from __future__ import annotations
import csv,hashlib,json,os,sqlite3
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SEED_ORDER=['sources','airports','operators','aircraft','parts','part_effectivity','fault_catalog','providers','inventory_lots','engineers','authorizations','engineer_shifts','tool_assets','task_requirements','flights','defects','work_orders','open_deferrals','logistics_quotes','fleet_status','communications','documents','doc_chunks']
def db_path():return Path(os.getenv('DEMO_DB_PATH',str(ROOT/'runtime/demo.sqlite')))
def connect(path=None):
 p=Path(path or db_path());p.parent.mkdir(parents=True,exist_ok=True)
 c=sqlite3.connect(p,timeout=20);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');c.execute('PRAGMA busy_timeout=20000');return c

def seed_database(path,scenario='nominal'):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():path.unlink()
 c=connect(path);c.executescript((ROOT/'database/schema.sql').read_text())
 for table in SEED_ORDER:
  info={r['name']:r['type'] for r in c.execute(f'PRAGMA table_info({table})')}
  with (ROOT/'data/seed'/f'{table}.csv').open(encoding='utf-8',newline='') as f:
   reader=csv.DictReader(f);fields=reader.fieldnames
   sql=f"INSERT INTO {table} ({','.join(fields)}) VALUES ({','.join('?' for _ in fields)})"
   for row in reader:
    vals=[]
    for col in fields:
     val=row[col]
     vals.append(None if val=='' else (int(val) if info[col]=='INTEGER' else float(val) if info[col]=='REAL' else val))
    c.execute(sql,vals)
 c.execute('INSERT INTO chunks_fts(chunk_id,section,content) SELECT chunk_id,section,content FROM doc_chunks')
 if scenario not in {p.stem for p in (ROOT/'data/scenarios').glob('*.json')}:raise ValueError('Unknown scenario')
 spec=json.loads((ROOT/f'data/scenarios/{scenario}.json').read_text())
 for item in spec['overrides']:
  table=item['table']
  if table not in SEED_ORDER:raise ValueError('Invalid fixture table')
  info=list(c.execute(f'PRAGMA table_info({table})'));pk=next(x['name'] for x in info if x['pk']);cols={x['name'] for x in info}
  if not set(item['values'])<=cols:raise ValueError('Invalid fixture column')
  c.execute(f"UPDATE {table} SET "+','.join(f'{k}=?' for k in item['values'])+f' WHERE {pk}=?',list(item['values'].values())+[item['key']])
 c.commit()
 errors=list(c.execute('PRAGMA foreign_key_check'))
 if errors:raise RuntimeError(f'Foreign key errors: {errors}')
 c.close();return spec

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
def now():return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def audit(c,actor,case_id,action,details,scenario_time):
 previous=c.execute('SELECT entry_hash FROM audit ORDER BY audit_id DESC LIMIT 1').fetchone()
 prev=previous['entry_hash'] if previous else '0'*64
 entry={'recorded_at_utc':now(),'scenario_time_utc':scenario_time,'actor':actor,'case_id':case_id,'action':action,'detail_json':canonical(details),'previous_hash':prev}
 entry['entry_hash']=digest(entry)
 c.execute('INSERT INTO audit(recorded_at_utc,scenario_time_utc,actor,case_id,action,detail_json,previous_hash,entry_hash) VALUES(?,?,?,?,?,?,?,?)',tuple(entry.values()))

def verify_audit(c):
 prev='0'*64
 for row in c.execute('SELECT * FROM audit ORDER BY audit_id'):
  r=dict(row);r.pop('audit_id');h=r.pop('entry_hash')
  if r['previous_hash']!=prev or digest(r)!=h:return False
  prev=h
 return True

def fetch(c,sql,args=()):return [dict(x) for x in c.execute(sql,args)]
def one(c,sql,args=()):
 r=c.execute(sql,args).fetchone();return dict(r) if r else None
