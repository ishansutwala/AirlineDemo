from __future__ import annotations
import json,os
from datetime import datetime,timedelta
from .db import ROOT,fetch,one,digest
from .retrieval import search
from . import model
POLICY=json.loads((ROOT/'config/policy.json').read_text())
def dt(s):return datetime.fromisoformat(s.replace('Z','+00:00'))
def iso(d):return d.strftime('%Y-%m-%dT%H:%M:%SZ')
def plus(s,m):return iso(dt(s)+timedelta(minutes=m))
def age(clock,value):return (dt(clock)-dt(value)).total_seconds()/60

def gate(event,clock):
 a=event['planning_authorization'];reasons=[]
 if a['status']!='ENABLED':reasons.append('Planning permission is not enabled.')
 if not a['issued_at']<=clock<a['expires_at']:reasons.append('Planning authorization is not current.')
 if a['scope']!='GROUND_PREPARATION_ONLY':reasons.append('Scope mismatch.')
 if event['safety_event_active']:reasons.append('External safety-event flag blocks this demo workflow.')
 return reasons

def inventory(c,event,ac,clock,part):
 effects=fetch(c,'SELECT * FROM part_effectivity WHERE part_id=? AND operator_id=? AND aircraft_type=? AND config_code=? AND valid_from<=? AND valid_to>?',(part,event['operator_id'],ac['aircraft_type'],ac['config_code'],clock,clock))
 results=[]
 for r in fetch(c,'SELECT * FROM inventory_lots WHERE part_id=? AND operator_id=? ORDER BY station,lot_id',(part,event['operator_id'])):
  reasons=[]
  if not effects:reasons.append('No applicable part effectivity.')
  if r['condition']!='SERVICEABLE':reasons.append('Condition '+r['condition'])
  if r['release_doc_status']!='VERIFIED':reasons.append('Release documents not verified.')
  if r['expiry_utc']<=clock:reasons.append('Lot expired.')
  if r['owner_type']!='OWNED' and not r['borrow_approved']:reasons.append('Pool/borrowing not authorized.')
  if not 0<=age(clock,r['last_verified_at'])<=POLICY['inventory_max_age_minutes']:reasons.append('Inventory snapshot stale or future-dated.')
  if r['qty_on_hand']-r['qty_reserved']<=0:reasons.append('No unreserved quantity.')
  results.append({**r,'eligible':not reasons,'usable_quantity':max(0,r['qty_on_hand']-r['qty_reserved']) if not reasons else 0,'rejection_reasons':reasons})
 return results

def staff(c,event,ac,clock,task,stand):
 rows=fetch(c,"""SELECT a.*,e.name,s.shift_id,s.start_utc,s.end_utc,s.busy_until_utc,s.last_verified_at FROM authorizations a
 JOIN engineers e ON a.engineer_id=e.engineer_id JOIN engineer_shifts s ON e.engineer_id=s.engineer_id
 WHERE a.operator_id=? AND a.station=? AND s.station=? AND s.start_utc<=? AND s.end_utc>? AND e.employment_status='ACTIVE'""",(event['operator_id'],event['destination'],event['destination'],stand,stand))
 output=[]
 for r in rows:
  reasons=[]
  for field in ['aircraft_type','config_code']:
   if r[field]!=ac[field]:reasons.append(field+' mismatch')
  if r['task_scope']!=task['task_scope']:reasons.append('Task authorization mismatch')
  if r['status']!='ACTIVE' or not r['valid_from']<=stand<r['valid_to']:reasons.append('Authorization not current')
  if not 0<=age(clock,r['last_verified_at'])<=POLICY['roster_max_age_minutes']:reasons.append('Roster stale')
  start=max(plus(stand,POLICY['stand_access_minutes']),r['busy_until_utc'],r['start_utc'])
  duration=sum(task[x] for x in ['inspection_minutes','resolution_minutes','verification_minutes','recording_minutes'])
  end=plus(start,duration)
  if end>r['end_utc'] or end>=r['valid_to']:reasons.append('Whole work window not covered')
  output.append({**r,'eligible':not reasons,'available_for_task_utc':start,'rejection_reasons':reasons})
 return output

def tooling(c,event,clock,task,stand):
 out=[]
 for r in fetch(c,'SELECT * FROM tool_assets WHERE station=? AND tool_code=?',(event['destination'],task['tool_code'])):
  reasons=[]
  if r['condition']!='SERVICEABLE':reasons.append('Tool not serviceable')
  if r['calibration_expiry_utc']<=stand:reasons.append('Calibration expired')
  if not 0<=age(clock,r['last_verified_at'])<=POLICY['tool_max_age_minutes']:reasons.append('Tool snapshot stale')
  out.append({**r,'eligible':not reasons,'rejection_reasons':reasons})
 return out

def logistics(c,event,clock,part,lots):
 stations={r['station'] for r in lots if r['eligible']};out=[]
 for q in fetch(c,'SELECT * FROM logistics_quotes WHERE part_id=? AND destination=?',(part,event['destination'])):
  reasons=[];ready=None
  if q['origin'] not in stations:reasons.append('No eligible stock at source')
  if q['valid_until_utc']<=clock:reasons.append('Quote expired')
  if not q['capacity_confirmed'] or not q['customs_ready']:reasons.append('Capacity or documentation unconfirmed')
  staged=plus(max(clock,q['available_from_utc']),q['source_prep_minutes'])
  if q['mode']=='AIR':
   if staged>q['cutoff_utc']:reasons.append('Tender cutoff missed')
   if q['departure_utc']<=clock:reasons.append('Movement already departed')
   ready=plus(q['arrival_utc'],q['destination_handling_minutes'])
  else:ready=plus(staged,q['transit_minutes']+q['destination_handling_minutes'])
  out.append({**q,'eligible':not reasons,'source_ready_utc':staged,'part_at_station_utc':ready if not reasons else None,'rejection_reasons':reasons})
 return sorted(out,key=lambda x:(not x['eligible'],x['part_at_station_utc'] or '9999'))

def alternates(c,event,ac,clock,nextflight):
 out=[]
 for r in fetch(c,"""SELECT a.*,f.station,f.available_from_utc,f.allocated_flight_id,f.status AS fleet_status,f.compatible_crew,f.last_verified_at FROM aircraft a JOIN fleet_status f ON a.aircraft_id=f.aircraft_id WHERE a.operator_id=? AND a.aircraft_id<>? AND f.station=?""",(event['operator_id'],ac['aircraft_id'],event['destination'])):
  reasons=[]
  if r['aircraft_type']!=ac['aircraft_type'] or r['config_code']!=ac['config_code']:reasons.append('Aircraft/configuration or crew compatibility requires separate review')
  if not r['compatible_crew']:reasons.append('Compatible crew unavailable')
  if r['seat_capacity']<nextflight['passengers']:reasons.append('Insufficient seat capacity')
  if r['allocated_flight_id'] or r['fleet_status']!='UNALLOCATED':reasons.append('Committed to another rotation; no uncommitted spare')
  if r['available_from_utc']>nextflight['scheduled_out_utc']:reasons.append('Not available before departure')
  if not 0<=age(clock,r['last_verified_at'])<=30:reasons.append('Fleet status stale')
  out.append({**r,'eligible':not reasons,'rejection_reasons':reasons})
 return out

def departure(nextflight,maintenance_ready):
 readiness=max(maintenance_ready,nextflight['other_turnaround_ready_utc'])
 dep=max(nextflight['scheduled_out_utc'],plus(readiness,nextflight['dispatch_buffer_minutes']))
 return {'maintenance_ready_utc':maintenance_ready,'estimated_departure_utc':dep,'delay_minutes':round(age(dep,nextflight['scheduled_out_utc']),1),'calculation_basis':'Synthetic task/logistics durations; max of parallel readiness paths plus dispatch buffer; not a flight release.'}

def build_plan(c,event,clock,mode='reference'):
 reasons=gate(event,clock)
 if reasons:return {'status':'BLOCKED','blocking_gaps':reasons,'options':[],'preparation_only':True,'dispatch_eligibility':'UNKNOWN'}
 ac=one(c,'SELECT * FROM aircraft WHERE aircraft_id=? AND operator_id=?',(event['aircraft_id'],event['operator_id']))
 inbound=one(c,'SELECT * FROM flights WHERE flight_id=? AND operator_id=?',(event['flight_id'],event['operator_id']))
 onward=one(c,'SELECT * FROM flights WHERE flight_id=? AND operator_id=?',(event['next_flight_id'],event['operator_id']))
 if not ac or not inbound or not onward:raise ValueError('Aircraft/flight/operator reference mismatch')
 if inbound['aircraft_id']!=ac['aircraft_id'] or onward['aircraft_id']!=ac['aircraft_id'] or inbound['destination']!=event['destination'] or onward['origin']!=event['destination']:
  return {'status':'BLOCKED_EVIDENCE','blocking_gaps':['Flight/tail/destination links do not match. Replan after externally updated rotation.'],'options':[],'preparation_only':True,'dispatch_eligibility':'UNKNOWN'}
 task=one(c,'SELECT * FROM task_requirements WHERE fault_code=? AND aircraft_type=? AND config_code=?',(event['fault_code'],ac['aircraft_type'],ac['config_code']))
 fault=one(c,'SELECT * FROM fault_catalog WHERE fault_code=?',(event['fault_code'],))
 if not task or not fault:return {'status':'BLOCKED_EVIDENCE','blocking_gaps':['No approved simulation planning template for this event/type/configuration.'],'options':[],'preparation_only':True,'dispatch_eligibility':'UNKNOWN'}
 model_trace=[];queries=['cabin zone temperature indication maintenance history ground preparation MEL review']
 if mode=='ollama':queries,trace=model.plan_search(event);model_trace.append({'phase':'search_planning',**trace})
 embedmodel=os.getenv('EMBEDDING_MODEL','nomic-embed-text');vector=None
 if mode=='ollama' and os.getenv('ENABLE_SEMANTIC','0')=='1':vector=model.embed([' '.join(queries)],embedmodel)[0]
 docs=search(c,event['operator_id'],ac['aircraft_type'],ac['config_code'],event['destination'],clock,' '.join(queries),query_vector=vector,embedding_model=embedmodel)
 history=fetch(c,'SELECT * FROM defects WHERE aircraft_id=? AND fault_code=? AND reported_at<? ORDER BY reported_at DESC LIMIT 8',(ac['aircraft_id'],fault['fault_code'],clock))
 for x in history:x['days_before_scenario']=int(age(event['occurred_at'],x['reported_at'])//1440)
 open_items=fetch(c,'SELECT * FROM open_deferrals WHERE aircraft_id=? AND status=\'OPEN\'',(ac['aircraft_id'],))
 lots=inventory(c,event,ac,clock,fault['part_id']);people=staff(c,event,ac,clock,task,inbound['estimated_inblock_utc']);tools=tooling(c,event,clock,task,inbound['estimated_inblock_utc']);quotes=logistics(c,event,clock,fault['part_id'],lots);swaps=alternates(c,event,ac,clock,onward)
 gaps=[]
 if 'PLANNING' not in docs['eligible_doc_types']:gaps.append('Current applicable trusted planning document unavailable.')
 if 'DISPATCH_REVIEW' not in docs['eligible_doc_types']:gaps.append('Current dispatch-review evidence checklist unavailable; no MEL-related conclusion permitted.')
 goodpeople=sorted((x for x in people if x['eligible']),key=lambda x:x['available_for_task_utc']);goodtools=sorted((x for x in tools if x['eligible']),key=lambda x:x['available_from_utc'])
 if not goodpeople:gaps.append('No currently authorized engineer covers this work window.')
 if not goodtools:gaps.append('No serviceable in-calibration tool available.')
 options=[];selected_eng=goodpeople[0] if goodpeople else None;selected_tool=goodtools[0] if goodtools else None
 if selected_eng and selected_tool:
  start=max(selected_eng['available_for_task_utc'],selected_tool['available_from_utc'])
  dur=sum(task[k] for k in ['inspection_minutes','resolution_minutes','verification_minutes','recording_minutes'])
  end=plus(start,dur)
  if end>selected_eng['end_utc'] or end>=selected_eng['valid_to'] or end>=selected_tool['calibration_expiry_utc']:gaps.append('Combined resource window is not fully covered.')
  options.append({'option_id':'A','name':'Prepare inspection and possible local resolution','status':'CONDITIONAL_ON_PHYSICAL_FINDINGS','start_utc':start,**departure(onward,end),'conditions':['Authorized physical inspection determines action.','No component replacement assumed in this branch; not a predicted root cause.'],'evidence_ids':['SIM-PROC-21-R3#S01','SIM-PROC-21-R3#S03','SIM-PROC-21-R3#S05','SIM-AUTH-R1#S01','SIM-SOP-REC-R1#S01',selected_eng['authorization_id'],selected_tool['tool_asset_id']]})
 options.append({'option_id':'B','name':'Prepare post-arrival MEL evidence review','status':'REVIEW_ONLY','dispatch_eligibility':'UNKNOWN','estimated_departure_utc':None,'conditions':['This fixture supplies no real operator MEL item.','Authorized dispatch determination and interaction review remain external.'],'evidence_ids':['SIM-MEL-21-R2#S01','SIM-MEL-21-R2#S02','SIM-SOP-REC-R1#S01']})
 validquotes=[q for q in quotes if q['eligible']]
 contingency=None
 if validquotes and selected_eng and selected_tool:
  q=validquotes[0];lot=next(x for x in lots if x['station']==q['origin'] and x['eligible'])
  start=max(q['part_at_station_utc'],selected_eng['available_for_task_utc'],selected_tool['available_from_utc']);end=plus(start,task['replacement_minutes'])
  can= end<=selected_eng['end_utc'] and end<selected_eng['valid_to'] and end<selected_tool['calibration_expiry_utc']
  options.append({'option_id':'C','name':'Component movement and replacement contingency','status':'QUOTED_CONTINGENCY' if can else 'NEEDS_NEW_RESOURCE_WINDOW','quote_id':q['quote_id'],'lot_id':lot['lot_id'],'part_at_station_utc':q['part_at_station_utc'],'start_utc':start,**departure(onward,end),'conditions':['Shipment not booked by this demo.','Physical finding must justify replacement.','Quote and inventory must be refreshed before commitment.'],'evidence_ids':['SIM-STORES-R1#S01','SIM-LOG-AMS-R1#S01','SIM-PROC-21-R3#S04',q['quote_id'],lot['lot_id']]})
  contingency={'lot_id':lot['lot_id'],'lot_version':lot['row_version'],'quote_id':q['quote_id'],'quantity':1}
 else:options.append({'option_id':'C','name':'Component movement contingency','status':'NO_VALID_CONTINGENCY','conditions':['No usable combination of stock, transport and local resources.'],'evidence_ids':['SIM-STORES-R1#S01','SIM-LOG-AMS-R1#S01']})
 options.append({'option_id':'D','name':'Aircraft swap referral','status':'OCC_REVIEW_REQUIRED' if any(x['eligible'] for x in swaps) else 'NO_UNCOMMITTED_COMPATIBLE_AIRCRAFT','conditions':['No automatic tail swap.','Aircraft presence alone is not availability.'],'evidence_ids':['SIM-OCC-R1#S01','SIM-FRA-STA-R1#S01']})
 ids=[event['event_id'],event.get('fault_code',''),fault.get('part_id',''),ac['aircraft_id'],inbound['flight_id'],onward['flight_id'],task['task_id']]+[o['option_id'] for o in options]
 ids += [c for opt in options for c in opt.get('evidence_ids', [])]
 ids += [x['chunk_id'] for x in docs['chunks']]+[x['doc_id'] for x in docs['chunks']]+[x['defect_id'] for x in history]+[x['lot_id'] for x in lots]+[x['part_id'] for x in lots]+[x['authorization_id'] for x in people]+[x['engineer_id'] for x in people]+[x['tool_asset_id'] for x in tools]+[x['quote_id'] for x in quotes]+[x['aircraft_id'] for x in swaps]+[x['deferral_id'] for x in open_items]
 ids=[x for x in ids if x]
 plan={'status':'BLOCKED_EVIDENCE' if gaps else 'AWAITING_APPROVAL','built_at_scenario_utc':clock,'expires_at_scenario_utc':min(plus(clock,POLICY['plan_ttl_minutes']),event['planning_authorization']['expires_at']),'preparation_only':True,'dispatch_eligibility':'UNKNOWN','mode':mode,'retrieval_mode':docs['mode'],'blocking_gaps':gaps,'aircraft':ac,'inbound':inbound,'onward':onward,'history':history,'open_deferrals':open_items,'documents':docs['chunks'],'inventory':lots,'engineers':people,'tools':tools,'logistics':quotes,'alternate_aircraft':swaps,'options':options,'selected_engineer_id':selected_eng['engineer_id'] if selected_eng else None,'selected_tool_id':selected_tool['tool_asset_id'] if selected_tool else None,'contingency':contingency,'allowed_evidence_ids':sorted(set(ids)),'tool_trace':[{'tool':name,'status':'COMPLETED'} for name in ['get_event','get_rotation','get_history','search_documents','check_inventory','check_engineers','check_tools','quote_logistics','evaluate_alternates','calculate_options']]}
 if mode=='ollama' and not gaps:
  brief={k:plan[k] for k in ['options','history','open_deferrals','inventory','documents','allowed_evidence_ids']}
  explanation,trace=model.explain(brief);plan['explanation']=explanation;model_trace.append({'phase':'evidence_summary',**trace})
 else:plan['explanation']={'summary':'REFERENCE MODE - no model inference. Prepare FRA inspection and assemble the post-arrival dispatch-review evidence. Inspect the quarantined/usable inventory distinction and the resource-window constraints. Treat component movement as a contingency, not a promise of on-time return to service.','claims':[],'unresolved_questions':['Physical diagnosis and actual work requirement.','Actual applicable operator MEL and authorized dispatch assessment.'],'preparation_only':True,'dispatch_eligibility':'UNKNOWN'}
 plan['model_trace']=model_trace
 plan['model_output_warning']='Model prose is a draft for human review. Citation ID validation does not prove factual entailment. Deterministic fields and permissions are not model-editable.'
 return plan
