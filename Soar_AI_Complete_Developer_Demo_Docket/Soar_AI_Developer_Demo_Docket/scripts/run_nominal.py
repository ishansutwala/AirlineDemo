"""Exercise a running local demo. DESTRUCTIVELY resets only its demonstration database."""
from pathlib import Path
import argparse,json,os,sys,uuid
from urllib.parse import urlparse
import httpx

def main():
 p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8000');p.add_argument('--mode',choices=['reference','ollama'],default='reference');p.add_argument('--output',default='examples/nominal_case_export.json');a=p.parse_args()
 if urlparse(a.url).hostname not in ('127.0.0.1','localhost','::1'):raise SystemExit('This reset script only targets a local demo host.')
 def request(client,path,body,role):
  token=os.getenv('DEMO_'+role+'_TOKEN','demo-'+role.lower()+'-local');r=client.post(a.url+path,json=body,headers={'Authorization':'Bearer '+token});r.raise_for_status();return r.json()
 with httpx.Client(timeout=300,trust_env=False) as client:
  c=request(client,'/api/demo/load',{'scenario_id':'nominal'},'SIMULATOR');base='/api/cases/'+c['case_id']
  c=request(client,base+'/analyze',{'mode':a.mode},'MCC')
  if c['state']!='AWAITING_APPROVAL':raise SystemExit('Plan not approvable: '+c['state'])
  c=request(client,base+'/approve-preparation',{'case_version':c['version'],'plan_hash':c['plan_hash'],'idempotency_key':'cli-'+str(uuid.uuid4())},'MCC')
  for t in ['2026-09-14T06:30:00Z','2026-09-14T06:50:00Z']:c=request(client,base+'/advance-clock',{'clock_utc':t},'SIMULATOR')
  outcome=json.loads((Path(__file__).resolve().parents[1]/'data/events/outcome_success.json').read_text());c=request(client,base+'/external-outcome',outcome,'SIMULATOR')
  token=os.getenv('DEMO_VIEWER_TOKEN','demo-viewer-local');r=client.get(a.url+base+'/export',headers={'Authorization':'Bearer '+token});r.raise_for_status();c=r.json()
 out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(c,indent=2)+'\n',encoding='utf-8');print(json.dumps({'case_id':c['case_id'],'state':c['state'],'mode':c['analysis_mode'],'audit_hash_chain_valid':c['audit_hash_chain_valid'],'export':str(out)},indent=2))
if __name__=='__main__':main()
