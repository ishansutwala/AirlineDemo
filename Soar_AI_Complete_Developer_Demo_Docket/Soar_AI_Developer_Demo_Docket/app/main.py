from __future__ import annotations
import json,os,uuid,hmac
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import FastAPI,Depends,HTTPException,Header,Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from . import db,engine,model
from .schemas import Event,Load,Analyze,Approve,Update,Advance,Outcome,FlightCreate,FlightUpdate

ROLES={
 'MCC':('DEMO_MCC_TOKEN','demo-mcc-local'),
 'OCC':('DEMO_OCC_TOKEN','demo-occ-local'),
 'VIEWER':('DEMO_VIEWER_TOKEN','demo-viewer-local'),
 'SIMULATOR':('DEMO_SIMULATOR_TOKEN','demo-simulator-local')}
def actor(authorization:Annotated[str|None,Header()]=None):
 if not authorization or not authorization.startswith('Bearer '):raise HTTPException(401,'Use a local-demo bearer token.')
 token=authorization[7:]
 for role,(name,default) in ROLES.items():
  if hmac.compare_digest(token,os.getenv(name,default)):return role
 raise HTTPException(401,'Unknown local-demo bearer token.')
def require(role,allowed):
 if role not in allowed:raise HTTPException(403,'Role cannot perform this action.')
def row_case(c,cid):
 row=db.one(c,'SELECT * FROM cases WHERE case_id=? AND operator_id=?',(cid,'SIM-AIR'))
 if not row:raise HTTPException(404,'Case not found for this operator.')
 return row

def view_case(c,cid):
 row=row_case(c,cid);row['event']=json.loads(row.pop('event_json'));row['plan']=json.loads(row.pop('plan_json')) if row['plan_json'] else None
 row['inbound_flight']=db.one(c,'SELECT * FROM flights WHERE flight_id=?',(row['event']['flight_id'],))
 row['onward_flight']=db.one(c,'SELECT * FROM flights WHERE flight_id=?',(row['event']['next_flight_id'],))
 row['aircraft']=db.one(c,'SELECT * FROM aircraft WHERE aircraft_id=?',(row['event']['aircraft_id'],))
 if row['inbound_flight']:row['origin_airport']=db.one(c,'SELECT * FROM airports WHERE iata=?',(row['inbound_flight']['origin'],))
 row['dest_airport']=db.one(c,'SELECT * FROM airports WHERE iata=?',(row['event']['destination'],))
 row['approvals']=db.fetch(c,'SELECT * FROM approvals WHERE case_id=?',(cid,));row['reservations']=db.fetch(c,'SELECT * FROM reservations WHERE case_id=?',(cid,));row['outbox']=db.fetch(c,'SELECT * FROM outbox WHERE case_id=?',(cid,));row['audit']=db.fetch(c,'SELECT * FROM audit WHERE case_id=? ORDER BY audit_id',(cid,));return row


def merge(a,b):
 out=json.loads(json.dumps(a))
 for k,v in b.items():out[k]=merge(out[k],v) if isinstance(v,dict) and isinstance(out.get(k),dict) else v
 return out

def create_case(c,e,clock,scenario,role):
 event=Event.model_validate(e).model_dump()
 if event['operator_id']!='SIM-AIR':raise HTTPException(403,'Demo tenant is SIM-AIR.')
 if event['occurred_at']>clock:raise HTTPException(422,'Event timestamp is ahead of scenario clock.')
 for fid in (event['flight_id'],event['next_flight_id']):
  f=db.one(c,'SELECT * FROM flights WHERE flight_id=? AND operator_id=?',(fid,'SIM-AIR'))
  if not f or f['aircraft_id']!=event['aircraft_id']:raise HTTPException(422,'Flight, aircraft and operator linkage must match.')
 prior=db.one(c,'SELECT case_id,event_hash FROM cases WHERE event_id=?',(event['event_id'],))
 if prior:
  if prior['event_hash']!=db.digest(event):raise HTTPException(409,'Event ID reused with different payload. Use the update endpoint with a higher sequence.')
  return prior['case_id']
 cid='CASE-'+event['event_id'];state='BLOCKED' if engine.gate(event,clock) else 'CREATED'
 c.execute('INSERT INTO cases(case_id,operator_id,aircraft_id,event_id,event_hash,event_json,scenario_id,clock_utc,state,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)',(cid,'SIM-AIR',event['aircraft_id'],event['event_id'],db.digest(event),db.canonical(event),scenario,clock,state,db.now()))
 db.audit(c,role,cid,'EVENT_RECEIVED',{'source':event['source_system'],'state':state},clock);return cid

def release_holds(c,cid,reason,clock):
 for r in db.fetch(c,"SELECT * FROM reservations WHERE case_id=? AND status='HELD'",(cid,)):
  c.execute('UPDATE inventory_lots SET qty_reserved=qty_reserved-?,row_version=row_version+1 WHERE lot_id=? AND qty_reserved>=?',(r['quantity'],r['lot_id'],r['quantity']))
  c.execute("UPDATE reservations SET status='RELEASED' WHERE reservation_id=?",(r['reservation_id'],))
  db.audit(c,'SYSTEM',cid,'HOLD_RELEASED',{'lot_id':r['lot_id'],'reason':reason},clock)

@asynccontextmanager
async def lifespan(app):
 if not db.db_path().exists():db.seed_database(db.db_path())
 yield
app=FastAPI(title='Soar.AI Ground Recovery Demo',version='1.0.0',description='Fictional demo only. No aircraft control or real dispatch decisions. Local sample tokens are not production authentication.',docs_url=None,redoc_url=None,lifespan=lifespan)
app.mount('/static',StaticFiles(directory=db.ROOT/'app/static'),name='static')
@app.middleware('http')
async def security_headers(request,call_next):
 response=await call_next(request)
 response.headers['X-Content-Type-Options']='nosniff';response.headers['Cache-Control']='no-store'
 response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-src 'self'; base-uri 'none'"
 return response
@app.get('/')
def home():return FileResponse(db.ROOT/'app/static/index.html')
@app.get('/api/health')
def health():return {'status':'ok','simulation':True,'model_weights_bundled':False,'default_inference':'REFERENCE_ONLY_NO_AI'}
@app.get('/api/meta')
def meta():
 return {'scenario_date':'2026-09-14','timezone_display':'Europe/Berlin','scenarios':[{'id':p.stem,'name':json.loads(p.read_text())['name']} for p in sorted((db.ROOT/'data/scenarios').glob('*.json'))],'roles':list(ROLES),'safety':'Ground preparation only. No SLM onboard. No flight-safety, dispatch or maintenance-release authority.'}
@app.post('/api/demo/load')
def load(body:Load,role=Depends(actor)):
 require(role,['SIMULATOR'])
 if body.scenario_id not in {p.stem for p in (db.ROOT/'data/scenarios').glob('*.json')}:raise HTTPException(404,'Unknown scenario')
 # Single-user demo reset only. Never expose this operation to a production system.
 spec=db.seed_database(db.db_path(),body.scenario_id)
 e=merge(json.loads((db.ROOT/spec['event_file']).read_text()),spec['event_patch'])
 with db.connect() as c:
  cid=create_case(c,e,spec['clock_utc'],body.scenario_id,role);c.commit();return view_case(c,cid)

@app.post('/api/demo/load-flight/{flight_id}')
def load_flight_case(flight_id:str,role=Depends(actor)):
 require(role,['SIMULATOR','MCC','OCC'])
 with db.connect() as c:
  f=db.one(c,'SELECT * FROM flights WHERE flight_id=?',(flight_id,))
  if not f:raise HTTPException(404,'Flight not found.')
  next_f=db.one(c,'SELECT * FROM flights WHERE aircraft_id=? AND origin=? AND flight_id<>? ORDER BY scheduled_out_utc',(f['aircraft_id'],f['destination'],f['flight_id']))
  next_fid=next_f['flight_id'] if next_f else f['flight_id']
  clock_utc=engine.plus(f['scheduled_out_utc'],min(60,max(10,int(engine.age(f['scheduled_in_utc'],f['scheduled_out_utc'])//2))))
  if clock_utc>f['estimated_inblock_utc']:clock_utc=engine.plus(f['estimated_inblock_utc'],-30)
  event={
   'schema_version':'1.0',
   'event_id':f'EV-{f["flight_id"]}',
   'source_system':'SIMULATED_MCC_ADAPTER',
   'source_sequence':1,
   'operator_id':f['operator_id'],
   'aircraft_id':f['aircraft_id'],
   'flight_id':f['flight_id'],
   'next_flight_id':next_fid,
   'destination':f['destination'],
   'occurred_at':f['scheduled_out_utc'],
   'received_at':clock_utc,
   'fault_code':'DEMO-25-019',
   'reported_symptom':f'In-flight cabin zone temperature sensor indication anomaly reported on {f["display_number"]} ({f["origin"]}->{f["destination"]}).',
   'crew_operational_status':'CREW_MONITORING_NO_FLIGHT_SAFETY_IMPACT',
   'planning_authorization':{
    'status':'ENABLED',
    'issued_by':'MCC_SUPERVISOR_SIM',
    'issued_at':f['scheduled_out_utc'],
    'expires_at':engine.plus(f['estimated_inblock_utc'],180),
    'scope':'GROUND_PREPARATION_ONLY'
   },
   'safety_event_active':False,
   'data_class':'SYNTHETIC',
   'note':f'Dynamically generated incident from flight {flight_id}'
  }
  cid=f'CASE-EV-{f["flight_id"]}'
  c.execute('DELETE FROM outbox WHERE case_id=?',(cid,))
  c.execute('DELETE FROM reservations WHERE case_id=?',(cid,))
  c.execute('DELETE FROM approvals WHERE case_id=?',(cid,))
  c.execute('DELETE FROM cases WHERE event_id=?',(f'EV-{f["flight_id"]}',))
  new_cid=create_case(c,event,clock_utc,'custom',role)
  c.commit()
  return view_case(c,new_cid)

@app.post('/api/events')
def events(event:Event,role=Depends(actor)):
 require(role,['SIMULATOR'])
 with db.connect() as c:
  cid=create_case(c,event.model_dump(),engine.POLICY['reference_clock_utc'],'custom',role);c.commit();return view_case(c,cid)
@app.get('/api/cases/{cid}')
def get_case(cid:str,role=Depends(actor)):
 with db.connect() as c:return view_case(c,cid)
@app.post('/api/cases/{cid}/analyze')
def analyze(cid:str,body:Analyze,role=Depends(actor)):
 require(role,['MCC'])
 with db.connect() as c:
  snap=row_case(c,cid)
  if snap['state'] in ['PREPARATION_APPROVED','ON_STAND','CLOSED']:raise HTTPException(409,'Do not overwrite an approved or completed case. Update/revoke or load a fresh fixture.')
  event=json.loads(snap['event_json'])
  try:plan=engine.build_plan(c,event,snap['clock_utc'],body.mode)
  except model.ModelFailure as exc:
   c.execute("UPDATE cases SET state='MODEL_ERROR',plan_json=NULL,plan_hash=NULL,analysis_mode=? WHERE case_id=?",(body.mode,cid));db.audit(c,role,cid,'MODEL_ERROR',{'message':str(exc)},snap['clock_utc']);c.commit()
   raise HTTPException(503,str(exc)) from exc
  c.execute('BEGIN IMMEDIATE')
  current=row_case(c,cid)
  if current['version']!=snap['version'] or current['event_hash']!=snap['event_hash'] or current['clock_utc']!=snap['clock_utc']:raise HTTPException(409,'Case changed during analysis. Re-run.')
  phash=db.digest(plan);version=snap['version']+1
  c.execute('UPDATE cases SET state=?,version=?,plan_json=?,plan_hash=?,analysis_mode=? WHERE case_id=?',(plan['status'],version,db.canonical(plan),phash,body.mode,cid))
  for trace in plan.get('tool_trace',[]):db.audit(c,'WORKFLOW',cid,'READ_TOOL',trace,snap['clock_utc'])
  db.audit(c,role,cid,'PLAN_PREPARED',{'mode':body.mode,'status':plan['status'],'plan_hash':phash,'model_requests':len(plan.get('model_trace',[]))},snap['clock_utc']);c.commit();return view_case(c,cid)
@app.post('/api/cases/{cid}/approve-preparation')
def approve(cid:str,body:Approve,role=Depends(actor)):
 require(role,['MCC'])
 with db.connect() as c:
  c.execute('BEGIN IMMEDIATE');row=row_case(c,cid)
  prior=db.one(c,'SELECT * FROM approvals WHERE idempotency_key=?',(body.idempotency_key,))
  if prior:
   if prior['case_id']!=cid or prior['plan_hash']!=body.plan_hash or prior['case_version']!=body.case_version:raise HTTPException(409,'Idempotency key reused for a different request.')
   if row['state'] not in ('PREPARATION_APPROVED','ON_STAND','CLOSED') or row['version']!=prior['case_version']:raise HTTPException(409,'Original approval was invalidated; no actions replayed.')
   return view_case(c,cid)
  if row['state']!='AWAITING_APPROVAL' or row['version']!=body.case_version or row['plan_hash']!=body.plan_hash:raise HTTPException(409,'Plan is no longer current or approvable.')
  plan=json.loads(row['plan_json']);event=json.loads(row['event_json']);clock=row['clock_utc']
  if engine.gate(event,clock) or clock>=plan['expires_at_scenario_utc']:raise HTTPException(409,'Permission or plan expired.')
  fresh=engine.build_plan(c,event,clock,'reference')
  if fresh['status']!='AWAITING_APPROVAL':raise HTTPException(409,'Required evidence/resources changed. Replan.')
  for field in ['selected_engineer_id','selected_tool_id','contingency','options']:
   if fresh.get(field)!=plan.get(field):raise HTTPException(409,'Resource snapshot changed. Replan.')
  if {(d['chunk_id'],d['sha256']) for d in fresh.get('documents',[])}!={(d['chunk_id'],d['sha256']) for d in plan.get('documents',[])}:
   # Search-query differences may change optional results in live mode; require the approved documents to remain current.
   valid={d['chunk_id']:d['sha256'] for d in __import__('app.retrieval',fromlist=['eligible_chunks']).eligible_chunks(c,'SIM-AIR',plan['aircraft']['aircraft_type'],plan['aircraft']['config_code'],event['destination'],clock)}
   if any(valid.get(d['chunk_id'])!=d['sha256'] for d in plan.get('documents',[])):raise HTTPException(409,'Document evidence changed or expired.')
  if plan.get('contingency'):
   x=plan['contingency']
   result=c.execute('UPDATE inventory_lots SET qty_reserved=qty_reserved+1,row_version=row_version+1 WHERE lot_id=? AND row_version=? AND qty_on_hand-qty_reserved>=1',(x['lot_id'],x['lot_version']))
   if result.rowcount!=1:raise HTTPException(409,'Inventory changed. No hold was made; replan.')
   c.execute('INSERT INTO reservations VALUES(?,?,?,?,?,?,?)',(str(uuid.uuid4()),cid,x['lot_id'],1,'HELD',clock,engine.plus(clock,engine.POLICY['hold_ttl_minutes'])))
  c.execute('INSERT INTO approvals VALUES(?,?,?,?,?,?,?,?)',(str(uuid.uuid4()),cid,row['version'],row['plan_hash'],role,'APPROVE_PREPARATION',clock,body.idempotency_key))
  for action,target in [('DRAFT_WORK_ORDER','SIM_MRO'),('SIMULATED_NOTIFY',event['destination']+'_MAINTENANCE'),('SIMULATED_NOTIFY','SIM_OCC')]:
   payload={'case_id':cid,'plan_hash':row['plan_hash'],'approved_by':role,'preparation_only':True,'external_delivery':False}
   c.execute('INSERT INTO outbox VALUES(?,?,?,?,?,?,?)',(str(uuid.uuid4()),cid,action,target,db.canonical(payload),'SIMULATED_ONLY',clock))
  c.execute("UPDATE cases SET state='PREPARATION_APPROVED' WHERE case_id=?",(cid,));db.audit(c,role,cid,'PREPARATION_APPROVED',{'plan_hash':row['plan_hash'],'no_dispatch_or_release_authority':True},clock);c.commit();return view_case(c,cid)
@app.post('/api/cases/{cid}/update')
def update_case(cid:str,body:Update,role=Depends(actor)):
 require(role,['SIMULATOR'])
 with db.connect() as c:
  c.execute('BEGIN IMMEDIATE');r=row_case(c,cid);e=json.loads(r['event_json'])
  if r['state']=='CLOSED':raise HTTPException(409,'Closed case cannot be rewritten.')
  if body.source_sequence<=e['source_sequence']:raise HTTPException(409,'Update must have a strictly newer source sequence.')
  e['source_sequence']=body.source_sequence
  if body.destination:
   if not db.one(c,'SELECT iata FROM airports WHERE iata=?',(body.destination,)):raise HTTPException(422,'Unknown destination.')
   e['destination']=body.destination
  if body.planning_status:e['planning_authorization']['status']=body.planning_status
  if body.safety_event_active is not None:e['safety_event_active']=body.safety_event_active
  # Any operational update invalidates this narrow demo plan. It does not determine safety.
  release_holds(c,cid,'Event/authority/destination update',r['clock_utc'])
  c.execute("UPDATE cases SET event_json=?,event_hash=?,state='SUSPENDED',version=version+1,plan_json=NULL,plan_hash=NULL WHERE case_id=?",(db.canonical(e),db.digest(e),cid));db.audit(c,role,cid,'CASE_SUSPENDED',body.model_dump(exclude_none=True),r['clock_utc']);c.commit();return view_case(c,cid)
@app.post('/api/cases/{cid}/advance-clock')
def advance(cid:str,body:Advance,role=Depends(actor)):
 require(role,['SIMULATOR'])
 with db.connect() as c:
  c.execute('BEGIN IMMEDIATE');r=row_case(c,cid)
  if body.clock_utc<r['clock_utc']:raise HTTPException(422,'Scenario clock cannot move backwards.')
  e=json.loads(r['event_json']);flight=db.one(c,'SELECT * FROM flights WHERE flight_id=?',(e['flight_id'],));state=r['state']
  if state=='PREPARATION_APPROVED' and body.clock_utc>=flight['estimated_inblock_utc']:state='ON_STAND'
  c.execute('UPDATE cases SET clock_utc=?,state=? WHERE case_id=?',(body.clock_utc,state,cid))
  expired=db.one(c,"SELECT reservation_id FROM reservations WHERE case_id=? AND status='HELD' AND expires_at<=?",(cid,body.clock_utc))
  if expired:release_holds(c,cid,'Hold expired',body.clock_utc)
  db.audit(c,role,cid,'SIMULATED_CLOCK_ADVANCED',{'state':state},body.clock_utc);c.commit();return view_case(c,cid)
@app.post('/api/cases/{cid}/external-outcome')
def external_outcome(cid:str,body:Outcome,role=Depends(actor)):
 require(role,['SIMULATOR'])
 with db.connect() as c:
  c.execute('BEGIN IMMEDIATE');r=row_case(c,cid)
  if r['state']!='ON_STAND':raise HTTPException(409,'Outcome can be recorded only after approved preparation and simulated arrival at stand.')
  if body.recorded_at<r['clock_utc']:raise HTTPException(422,'Outcome timestamp precedes scenario clock.')
  state='CLOSED' if body.status=='SERVICEABLE_RECORDED_EXTERNALLY' else 'ON_STAND'
  if state=='CLOSED':release_holds(c,cid,'External simulated completion; component unused',body.recorded_at)
  c.execute('UPDATE cases SET state=?,clock_utc=? WHERE case_id=?',(state,body.recorded_at,cid));db.audit(c,role,cid,'EXTERNAL_MAINTENANCE_STATUS',body.model_dump(),body.recorded_at);c.commit();return view_case(c,cid)
@app.get('/api/cases/{cid}/export')
def export_case(cid:str,role=Depends(actor)):
 with db.connect() as c:
  result=view_case(c,cid);result['audit_hash_chain_valid']=db.verify_audit(c);return result
@app.get('/api/data/{table}')
def data(table:str,limit:int=Query(default=30,ge=1,le=100),role=Depends(actor)):
 common={'airports','parts','engineers','tool_assets','fault_catalog','providers'}
 tenant={'aircraft','flights','inventory_lots','authorizations','documents','communications'}
 with db.connect() as c:
  if table in common:return db.fetch(c,f'SELECT * FROM {table} LIMIT ?',(limit,))
  if table in tenant:return db.fetch(c,f'SELECT * FROM {table} WHERE operator_id=? LIMIT ?',('SIM-AIR',limit))
  if table=='defects':return db.fetch(c,'SELECT d.* FROM defects d JOIN aircraft a ON d.aircraft_id=a.aircraft_id WHERE a.operator_id=? ORDER BY reported_at DESC LIMIT ?',('SIM-AIR',limit))
  raise HTTPException(404,'Table not exposed as a generic tool.')
@app.get('/api/documents/{doc_id}/pdf')
def document_pdf(doc_id:str,case_id:str,role=Depends(actor)):
 with db.connect() as c:
  r=row_case(c,case_id)
  if not r['plan_json']:raise HTTPException(409,'No approved evidence snapshot available.')
  plan=json.loads(r['plan_json'])
  if doc_id not in {d['doc_id'] for d in plan.get('documents',[])}:raise HTTPException(403,'Document is not in this case evidence snapshot.')
  d=db.one(c,'SELECT * FROM documents WHERE doc_id=? AND operator_id=?',(doc_id,'SIM-AIR'))
  path=(db.ROOT/d['pdf_path']).resolve()
  if not path.is_relative_to((db.ROOT/'knowledge/pdf').resolve()) or not path.exists():raise HTTPException(404,'Document PDF unavailable.')
  return FileResponse(path,media_type='application/pdf',filename=path.name)

@app.get('/api/flights')
def list_flights(aircraft_id:str|None=None,origin:str|None=None,destination:str|None=None,limit:int=Query(default=100,ge=1,le=300),role=Depends(actor)):
 with db.connect() as c:
  query='SELECT * FROM flights WHERE 1=1'
  params=[]
  if aircraft_id:
   query+=' AND aircraft_id=?'
   params.append(aircraft_id)
  if origin:
   query+=' AND origin=?'
   params.append(origin)
  if destination:
   query+=' AND destination=?'
   params.append(destination)
  query+=' ORDER BY scheduled_out_utc DESC LIMIT ?'
  params.append(limit)
  return db.fetch(c,query,tuple(params))

@app.get('/api/flights/{flight_id}')
def get_flight(flight_id:str,role=Depends(actor)):
 with db.connect() as c:
  f=db.one(c,'SELECT * FROM flights WHERE flight_id=?',(flight_id,))
  if not f:raise HTTPException(404,'Flight not found.')
  return f

@app.post('/api/flights')
def create_flight(body:FlightCreate,role=Depends(actor)):
 require(role,['SIMULATOR','MCC','OCC'])
 with db.connect() as c:
  c.execute('BEGIN IMMEDIATE')
  if db.one(c,'SELECT flight_id FROM flights WHERE flight_id=?',(body.flight_id,)):
   raise HTTPException(409,f'Flight ID {body.flight_id} already exists.')
  if not db.one(c,'SELECT operator_id FROM operators WHERE operator_id=?',(body.operator_id,)):
   raise HTTPException(422,f'Operator {body.operator_id} does not exist.')
  if not db.one(c,'SELECT aircraft_id FROM aircraft WHERE aircraft_id=?',(body.aircraft_id,)):
   raise HTTPException(422,f'Aircraft {body.aircraft_id} does not exist.')
  if not db.one(c,'SELECT iata FROM airports WHERE iata=?',(body.origin,)):
   raise HTTPException(422,f'Origin airport {body.origin} does not exist.')
  if not db.one(c,'SELECT iata FROM airports WHERE iata=?',(body.destination,)):
   raise HTTPException(422,f'Destination airport {body.destination} does not exist.')
  data=body.model_dump()
  cols=list(data.keys())
  c.execute(f"INSERT INTO flights ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})",list(data.values()))
  db.audit(c,role,None,'FLIGHT_CREATED',{'flight_id':body.flight_id,'route':f'{body.origin}->{body.destination}'},db.now())
  c.commit()
  return db.one(c,'SELECT * FROM flights WHERE flight_id=?',(body.flight_id,))

@app.put('/api/flights/{flight_id}')
def update_flight(flight_id:str,body:FlightUpdate,role=Depends(actor)):
 require(role,['SIMULATOR','MCC','OCC'])
 with db.connect() as c:
  c.execute('BEGIN IMMEDIATE')
  existing=db.one(c,'SELECT * FROM flights WHERE flight_id=?',(flight_id,))
  if not existing:raise HTTPException(404,f'Flight {flight_id} not found.')
  updates=body.model_dump(exclude_none=True)
  if not updates:return existing
  if 'origin' in updates and not db.one(c,'SELECT iata FROM airports WHERE iata=?',(updates['origin'],)):
   raise HTTPException(422,f'Origin airport {updates["origin"]} does not exist.')
  if 'destination' in updates and not db.one(c,'SELECT iata FROM airports WHERE iata=?',(updates['destination'],)):
   raise HTTPException(422,f'Destination airport {updates["destination"]} does not exist.')
  # validate timing if either changed
  sched_out=updates.get('scheduled_out_utc',existing['scheduled_out_utc'])
  sched_in=updates.get('scheduled_in_utc',existing['scheduled_in_utc'])
  if sched_out>=sched_in:raise HTTPException(422,'scheduled_out_utc must precede scheduled_in_utc')
  set_clause=','.join(f'{k}=?' for k in updates.keys())
  c.execute(f'UPDATE flights SET {set_clause} WHERE flight_id=?',list(updates.values())+[flight_id])
  db.audit(c,role,None,'FLIGHT_UPDATED',{'flight_id':flight_id,'updates':updates},db.now())
  c.commit()
  return db.one(c,'SELECT * FROM flights WHERE flight_id=?',(flight_id,))

@app.delete('/api/flights/{flight_id}')
def delete_flight(flight_id:str,role=Depends(actor)):
 require(role,['SIMULATOR','MCC','OCC'])
 with db.connect() as c:
  c.execute('BEGIN IMMEDIATE')
  existing=db.one(c,'SELECT * FROM flights WHERE flight_id=?',(flight_id,))
  if not existing:raise HTTPException(404,f'Flight {flight_id} not found.')
  c.execute('DELETE FROM flights WHERE flight_id=?',(flight_id,))
  db.audit(c,role,None,'FLIGHT_DELETED',{'flight_id':flight_id},db.now())
  c.commit()
  return {'status':'deleted','flight_id':flight_id}
