"""Validate the packaged fixture rather than treating a random-looking CSV as realistic."""
from pathlib import Path
import sys,json,hashlib
from datetime import datetime
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import db
checks=[]
def check(name,condition):
 checks.append({'check':name,'passed':bool(condition)})
with db.connect(db.ROOT/'database/seed.sqlite') as c:
 check('foreign keys',not db.fetch(c,'PRAGMA foreign_key_check'))
 check('integrity',c.execute('PRAGMA integrity_check').fetchone()[0]=='ok')
 for t in db.SEED_ORDER:
  count=c.execute(f'SELECT count(*) FROM {t}').fetchone()[0];check(t+' CSV row count',count==sum(1 for _ in __import__('csv').DictReader((db.ROOT/'data/seed'/f'{t}.csv').open(newline='',encoding='utf-8'))))
 check('stock never negative/over-reserved',not db.fetch(c,'SELECT lot_id FROM inventory_lots WHERE qty_on_hand<0 OR qty_reserved<0 OR qty_reserved>qty_on_hand'))
 check('passenger count within aircraft seats',not db.fetch(c,'SELECT flight_id FROM flights f JOIN aircraft a ON f.aircraft_id=a.aircraft_id WHERE f.passengers>a.seat_capacity'))
 check('flight timing order',not db.fetch(c,'SELECT flight_id FROM flights WHERE scheduled_out_utc>=estimated_landing_utc OR estimated_landing_utc>estimated_inblock_utc'))
 for ac in db.fetch(c,'SELECT * FROM aircraft'):
  fs=db.fetch(c,'SELECT * FROM flights WHERE aircraft_id=? ORDER BY scheduled_out_utc',(ac['aircraft_id'],))
  check(ac['aircraft_id']+' no overlapping rotations',all(a['estimated_inblock_utc']<=b['scheduled_out_utc'] and a['destination']==b['origin'] for a,b in zip(fs,fs[1:])))
 check('historical selected fleet effectivity',not db.fetch(c,"SELECT d.defect_id FROM defects d JOIN aircraft a ON d.aircraft_id=a.aircraft_id WHERE a.aircraft_type<>'A350-900' OR a.config_code<>'CAB-C01'"))
 for d in db.fetch(c,'SELECT * FROM documents'):
  m=db.ROOT/d['markdown_path'];p=db.ROOT/d['pdf_path'];check(d['doc_id']+' markdown hash',hashlib.sha256(m.read_bytes()).hexdigest()==d['sha256']);check(d['doc_id']+' PDF exists',p.exists() and p.stat().st_size>500)
 check('historical work-order time order',not db.fetch(c,'SELECT work_order_id FROM work_orders WHERE completed_at<=started_at'))
 check('all email fixtures use invalid test domain',all('example.invalid' in r['recipient'] and 'example.invalid' in r['sender'] for r in db.fetch(c,'SELECT * FROM communications')))
result={'status':'PASS' if all(x['passed'] for x in checks) else 'FAIL','check_count':len(checks),'checks':checks}
(db.ROOT/'qa/data_validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));sys.exit(0 if result['status']=='PASS' else 1)
