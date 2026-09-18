import json,sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo
import pytest
from app import db,engine,model
from app.schemas import Event,ModelExplanation
from app.retrieval import eligible_chunks,search

def load(client,h,name='nominal'):
 r=client.post('/api/demo/load',json={'scenario_id':name},headers=h['SIMULATOR']);assert r.status_code==200,r.text;return r.json()
def analyze(client,h,c,mode='reference'):
 r=client.post(f"/api/cases/{c['case_id']}/analyze",json={'mode':mode},headers=h['MCC']);assert r.status_code==200,r.text;return r.json()
def approve(client,h,c,key='test-approve-001'):
 return client.post(f"/api/cases/{c['case_id']}/approve-preparation",json={'case_version':c['version'],'plan_hash':c['plan_hash'],'idempotency_key':key},headers=h['MCC'])
def test_health_and_offline_ui(client):
 assert client.get('/api/health').json()['simulation'];r=client.get('/');assert r.status_code==200;assert 'NO SLM ONBOARD' in r.text;assert 'https://cdn' not in r.text

def test_seed_foreign_keys(client):
 with db.connect() as c:assert list(c.execute('PRAGMA foreign_key_check'))==[];assert c.execute('SELECT count(*) FROM defects').fetchone()[0]==300

def test_nominal_history_inventory_and_options(client,h):
 c=analyze(client,h,load(client,h));p=c['plan'];assert p['status']=='AWAITING_APPROVAL'
 assert p['history'][0]['defect_id']=='HIST-0042';assert p['history'][0]['days_before_scenario']==42
 assert sum(x['usable_quantity'] for x in p['inventory'] if x['station']=='FRA')==0
 assert sum(x['usable_quantity'] for x in p['inventory'] if x['station']=='AMS')==1
 opts={x['option_id']:x for x in p['options']};assert opts['A']['delay_minutes']==0;assert opts['C']['delay_minutes']==175
 assert opts['C']['part_at_station_utc']=='2026-09-14T10:20:00Z';assert opts['D']['status']=='NO_UNCOMMITTED_COMPATIBLE_AIRCRAFT'
 assert opts['B']['dispatch_eligibility']=='UNKNOWN';assert p['model_trace']==[]

def test_current_metadata_filters(client,h):
 c=analyze(client,h,load(client,h));text=json.dumps(c['plan']['documents'])
 for bad in ['OBSOLETE_CANARY','WRONG_TYPE_CANARY','WRONG_CONFIG_CANARY','FUTURE_CANARY','OTHER_TENANT_CANARY','INJECTION_CANARY']:assert bad not in text

def test_full_nominal_state_flow(client,h):
 c=analyze(client,h,load(client,h));r=approve(client,h,c);assert r.status_code==200,r.text;c=r.json()
 assert c['state']=='PREPARATION_APPROVED';assert len(c['reservations'])==1;assert len(c['outbox'])==3;assert all(x['status']=='SIMULATED_ONLY' for x in c['outbox'])
 r=client.post(f"/api/cases/{c['case_id']}/advance-clock",json={'clock_utc':'2026-09-14T06:50:00Z'},headers=h['SIMULATOR']);assert r.json()['state']=='ON_STAND'
 body=json.loads((db.ROOT/'data/events/outcome_success.json').read_text());r=client.post(f"/api/cases/{c['case_id']}/external-outcome",json=body,headers=h['SIMULATOR']);assert r.status_code==200,r.text;assert r.json()['state']=='CLOSED'
 assert r.json()['reservations'][0]['status']=='RELEASED'
 with db.connect() as con:assert db.verify_audit(con);assert con.execute("SELECT qty_reserved FROM inventory_lots WHERE lot_id='LOT-AMS-CZT-1'").fetchone()[0]==0

@pytest.mark.parametrize('role',['VIEWER','OCC','SIMULATOR'])
def test_only_mcc_can_approve(client,h,role):
 c=analyze(client,h,load(client,h));r=client.post(f"/api/cases/{c['case_id']}/approve-preparation",json={'case_version':c['version'],'plan_hash':c['plan_hash'],'idempotency_key':'denied-approval'},headers=h[role]);assert r.status_code==403

@pytest.mark.parametrize('role',['MCC','OCC','VIEWER'])
def test_only_simulator_ingests_events(client,h,role):
 e=json.loads((db.ROOT/'data/events/nominal.json').read_text());assert client.post('/api/events',json=e,headers=h[role]).status_code==403

@pytest.mark.parametrize('scenario',['no_authorization','critical_event','expired_authorization'])
def test_authority_fail_closed(client,h,scenario):
 c=analyze(client,h,load(client,h,scenario));assert c['state']=='BLOCKED';assert not c['plan']['options'];assert approve(client,h,c).status_code==409

@pytest.mark.parametrize('scenario',['no_engineer','no_tool','missing_current_document','unknown_fault'])
def test_missing_evidence_blocks_approval(client,h,scenario):
 c=analyze(client,h,load(client,h,scenario));assert c['state']=='BLOCKED_EVIDENCE';assert approve(client,h,c).status_code==409

def test_stale_inventory_not_used(client,h):
 p=analyze(client,h,load(client,h,'stale_inventory'))['plan'];ams=next(x for x in p['inventory'] if x['station']=='AMS');assert not ams['eligible'];assert p['contingency']['lot_id']=='LOT-CDG-CZT-1'

def test_missed_transport_cutoff_not_ignored(client,h):
 p=analyze(client,h,load(client,h,'late_cutoff'))['plan'];q=next(x for x in p['logistics'] if x['quote_id']=='Q-AMS-AIR');assert not q['eligible'];assert 'Tender cutoff missed' in q['rejection_reasons']

def test_busy_engineer_changes_critical_path(client,h):
 p=analyze(client,h,load(client,h,'busy_engineer'))['plan'];a=next(x for x in p['options'] if x['option_id']=='A');assert a['delay_minutes']==60

def test_no_parts_does_not_invent_contingency(client,h):
 p=analyze(client,h,load(client,h,'no_serviceable_parts'))['plan'];assert p['contingency'] is None;assert next(x for x in p['options'] if x['option_id']=='C')['status']=='NO_VALID_CONTINGENCY'

def test_approval_idempotency(client,h):
 c=analyze(client,h,load(client,h));assert approve(client,h,c).status_code==200;r=approve(client,h,c);assert r.status_code==200;assert len(r.json()['reservations'])==1;assert len(r.json()['approvals'])==1

def test_plan_hash_tampering_rejected(client,h):
 c=analyze(client,h,load(client,h));c['plan_hash']='0'*64;assert approve(client,h,c).status_code==409

def test_stale_plan_version_rejected(client,h):
 c=analyze(client,h,load(client,h));c['version']-=1;assert approve(client,h,c).status_code==409

def test_inventory_race_rejected_atomically(client,h):
 c=analyze(client,h,load(client,h))
 with db.connect() as con:con.execute("UPDATE inventory_lots SET qty_reserved=1,row_version=row_version+1 WHERE lot_id='LOT-AMS-CZT-1'")
 assert approve(client,h,c).status_code==409
 with db.connect() as con:assert con.execute('SELECT count(*) FROM approvals').fetchone()[0]==0

def test_resource_time_change_requires_replan(client,h):
 c=analyze(client,h,load(client,h))
 with db.connect() as con:con.execute("UPDATE engineer_shifts SET busy_until_utc='2026-09-14T09:00:00Z' WHERE shift_id='SHIFT-FRA-01-0'")
 assert approve(client,h,c).status_code==409

def test_revocation_invalidates_and_releases(client,h):
 c=analyze(client,h,load(client,h));assert approve(client,h,c).status_code==200
 r=client.post(f"/api/cases/{c['case_id']}/update",json={'source_sequence':2,'planning_status':'REVOKED'},headers=h['SIMULATOR']);assert r.status_code==200;r=r.json();assert r['state']=='SUSPENDED';assert r['plan'] is None;assert r['reservations'][0]['status']=='RELEASED'
 assert approve(client,h,c).status_code==409

def test_diversion_is_external_not_recommended(client,h):
 c=analyze(client,h,load(client,h));r=client.post(f"/api/cases/{c['case_id']}/update",json={'source_sequence':2,'destination':'VIE','planning_status':'DISABLED'},headers=h['SIMULATOR']);assert r.json()['event']['destination']=='VIE';assert r.json()['state']=='SUSPENDED'

def test_old_event_update_rejected(client,h):
 c=load(client,h);payload={'source_sequence':2,'planning_status':'DISABLED'};path=f"/api/cases/{c['case_id']}/update";assert client.post(path,json=payload,headers=h['SIMULATOR']).status_code==200;assert client.post(path,json=payload,headers=h['SIMULATOR']).status_code==409

def test_duplicate_event_id_is_idempotent(client,h):
 c=load(client,h);r=client.post('/api/events',json=c['event'],headers=h['SIMULATOR']);assert r.status_code==200;assert r.json()['case_id']==c['case_id']
 changed=dict(c['event']);changed['reported_symptom']='Different';assert client.post('/api/events',json=changed,headers=h['SIMULATOR']).status_code==409

def test_unknown_tenant_rejected(client,h):
 e=json.loads((db.ROOT/'data/events/nominal.json').read_text());e['operator_id']='OTHER-AIR';assert client.post('/api/events',json=e,headers=h['SIMULATOR']).status_code==403

def test_unauthenticated_read_denied(client):assert client.get('/api/data/aircraft').status_code==401

def test_operator_data_isolation(client,h):
 assert all(x['operator_id']=='SIM-AIR' for x in client.get('/api/data/documents?limit=100',headers=h['VIEWER']).json())
 assert client.get('/api/data/doc_chunks',headers=h['VIEWER']).status_code==404

def test_schema_does_not_accept_universal_safety_claim(client,h):
 e=json.loads((db.ROOT/'data/events/nominal.json').read_text());e['safe_to_fly']=True;assert client.post('/api/events',json=e,headers=h['SIMULATOR']).status_code==422

def test_utc_is_required(client,h):
 e=json.loads((db.ROOT/'data/events/nominal.json').read_text());e['occurred_at']='2026-09-14T08:05:00';assert client.post('/api/events',json=e,headers=h['SIMULATOR']).status_code==422

def test_timezones_and_schedule_window(client,h):
 c=analyze(client,h,load(client,h));p=c['plan'];s=datetime.fromisoformat(p['inbound']['scheduled_in_utc'].replace('Z','+00:00'))
 assert s.astimezone(ZoneInfo('Europe/Berlin')).strftime('%H:%M')=='08:50'
 assert (engine.dt(p['onward']['scheduled_out_utc'])-s).total_seconds()==130*60

def test_readiness_does_not_sum_parallel_turnaround_tasks(client,h):
 p=analyze(client,h,load(client,h))['plan'];a=next(x for x in p['options'] if x['option_id']=='A');assert a['maintenance_ready_utc']=='2026-09-14T07:35:00Z';assert a['estimated_departure_utc']=='2026-09-14T09:00:00Z'

def test_plan_expiration(client,h):
 c=analyze(client,h,load(client,h));client.post(f"/api/cases/{c['case_id']}/advance-clock",json={'clock_utc':'2026-09-14T06:40:00Z'},headers=h['SIMULATOR']);assert approve(client,h,c).status_code==409

def test_no_release_before_arrival(client,h):
 c=analyze(client,h,load(client,h));approve(client,h,c);body=json.loads((db.ROOT/'data/events/outcome_success.json').read_text());assert client.post(f"/api/cases/{c['case_id']}/external-outcome",json=body,headers=h['SIMULATOR']).status_code==409

def test_mcc_cannot_forge_external_release(client,h):
 c=load(client,h);body=json.loads((db.ROOT/'data/events/outcome_success.json').read_text());assert client.post(f"/api/cases/{c['case_id']}/external-outcome",json=body,headers=h['MCC']).status_code==403

def test_clock_cannot_run_backwards(client,h):
 c=load(client,h);assert client.post(f"/api/cases/{c['case_id']}/advance-clock",json={'clock_utc':'2026-09-14T06:00:00Z'},headers=h['SIMULATOR']).status_code==422

def test_expired_hold_released(client,h):
 c=analyze(client,h,load(client,h));approve(client,h,c);r=client.post(f"/api/cases/{c['case_id']}/advance-clock",json={'clock_utc':'2026-09-14T07:20:00Z'},headers=h['SIMULATOR']);assert r.json()['reservations'][0]['status']=='RELEASED'

def test_audit_update_delete_blocked(client,h):
 load(client,h)
 with db.connect() as c:
  with pytest.raises(sqlite3.IntegrityError):c.execute("UPDATE audit SET actor='bad'")
  with pytest.raises(sqlite3.IntegrityError):c.execute('DELETE FROM audit')
  assert db.verify_audit(c)

def test_remote_model_endpoint_rejected(monkeypatch):
 monkeypatch.setenv('OLLAMA_BASE_URL','https://example.com');
 with pytest.raises(model.ModelFailure):model.endpoint()

def test_cloud_model_rejected(monkeypatch):
 monkeypatch.setenv('OLLAMA_MODEL','anything:cloud')
 with pytest.raises(model.ModelFailure):model.model_tag()

def test_model_failure_is_explicit_no_fake_replay(client,h,monkeypatch):
 c=load(client,h)
 def fail(e):raise model.ModelFailure('Test model unavailable')
 monkeypatch.setattr(model,'plan_search',fail)
 r=client.post(f"/api/cases/{c['case_id']}/analyze",json={'mode':'ollama'},headers=h['MCC']);assert r.status_code==503
 r=client.get(f"/api/cases/{c['case_id']}",headers=h['MCC']).json();assert r['state']=='MODEL_ERROR';assert r['plan'] is None

def test_unknown_model_evidence_rejected(monkeypatch):
 def fake(*args):return ModelExplanation(summary='Draft.',claims=[{'text':'Claim','evidence_ids':['MADE-UP']}],unresolved_questions=[],dispatch_eligibility='UNKNOWN',preparation_only=True),{}
 monkeypatch.setattr(model,'call_json',fake)
 with pytest.raises(model.ModelFailure):model.explain({'allowed_evidence_ids':['REAL']})

def test_live_path_with_mocked_inference_preserves_rules(client,h,monkeypatch):
 # Contract test only. Not a local model quality/performance test.
 monkeypatch.setattr(model,'plan_search',lambda e:(['cabin indication maintenance review'],{'model':'TEST-DOUBLE'}))
 monkeypatch.setattr(model,'explain',lambda e:({'summary':'Test double only','claims':[],'unresolved_questions':[],'dispatch_eligibility':'UNKNOWN','preparation_only':True},{'model':'TEST-DOUBLE'}))
 c=analyze(client,h,load(client,h),'ollama');assert c['plan']['mode']=='ollama';assert len(c['plan']['model_trace'])==2;assert next(x for x in c['plan']['options'] if x['option_id']=='A')['delay_minutes']==0;assert approve(client,h,c).status_code==200

def test_noncanonical_timestamp_rejected(client,h):
 e=json.loads((db.ROOT/'data/events/nominal.json').read_text());e['occurred_at']='2026-09-14T06:05:00.250Z';assert client.post('/api/events',json=e,headers=h['SIMULATOR']).status_code==422

def test_permission_and_evidence_visible_in_ui(client):
 text=client.get('/').text
 assert 'eventDetails' in text and 'modelClaims' in text and 'flightsTable' in text

def test_flight_crud_endpoints(client,h):
 load(client,h)
 flt_data={
  'flight_id':'FLT-TEST-999',
  'operator_id':'SIM-AIR',
  'aircraft_id':'AC-001',
  'display_number':'SIM999',
  'origin':'DXB',
  'destination':'FRA',
  'scheduled_out_utc':'2026-09-14T01:00:00Z',
  'scheduled_in_utc':'2026-09-14T07:00:00Z',
  'estimated_landing_utc':'2026-09-14T06:50:00Z',
  'estimated_inblock_utc':'2026-09-14T07:00:00Z',
  'other_turnaround_ready_utc':'2026-09-14T00:40:00Z',
  'dispatch_buffer_minutes':20,
  'passengers':280,
  'crew_ready':1,
  'slot_confirmed':1,
  'status':'SCHEDULED',
  'source_basis':'Test flight',
  'data_class':'SYNTHETIC'
 }
 # Create
 r=client.post('/api/flights',json=flt_data,headers=h['SIMULATOR']);assert r.status_code==200,r.text;assert r.json()['flight_id']=='FLT-TEST-999'
 # Duplicate creation fails
 r_dup=client.post('/api/flights',json=flt_data,headers=h['SIMULATOR']);assert r_dup.status_code==409
 # Read
 r_get=client.get('/api/flights/FLT-TEST-999',headers=h['MCC']);assert r_get.status_code==200;assert r_get.json()['display_number']=='SIM999'
 r_list=client.get('/api/flights?origin=DXB',headers=h['MCC']);assert r_list.status_code==200;assert any(f['flight_id']=='FLT-TEST-999' for f in r_list.json())
 # Update
 r_up=client.put('/api/flights/FLT-TEST-999',json={'passengers':310,'status':'AIRBORNE'},headers=h['SIMULATOR']);assert r_up.status_code==200;assert r_up.json()['passengers']==310 and r_up.json()['status']=='AIRBORNE'
 # Delete
 r_del=client.delete('/api/flights/FLT-TEST-999',headers=h['SIMULATOR']);assert r_del.status_code==200
 r_gone=client.get('/api/flights/FLT-TEST-999',headers=h['MCC']);assert r_gone.status_code==404

