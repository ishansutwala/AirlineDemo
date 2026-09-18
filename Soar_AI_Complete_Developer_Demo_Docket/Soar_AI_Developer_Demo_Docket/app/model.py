"""Optional real local inference. No silent fallback to reference mode."""
from __future__ import annotations
import json,os
from urllib.parse import urlparse
import httpx
from .schemas import SearchPlan,ModelExplanation
from .db import ROOT
class ModelFailure(RuntimeError):pass

def endpoint():
 url=os.getenv('OLLAMA_BASE_URL','http://127.0.0.1:11434').rstrip('/')
 p=urlparse(url)
 allowed={'127.0.0.1','localhost','::1','host.docker.internal','ollama'}
 if p.scheme not in ('http','https') or p.hostname not in allowed or p.username or p.password or p.path:
  raise ModelFailure('Model endpoint must be an explicitly supported local host; no event-controlled URL is allowed.')
 return url

def model_tag():
 name=os.getenv('OLLAMA_MODEL','qwen2.5:7b')
 if 'cloud' in name.lower():raise ModelFailure('Cloud model names are forbidden for this demo.')
 return name


def call_json(system,user,schema):
 payload={'model':model_tag(),'messages':[{'role':'system','content':system},{'role':'user','content':json.dumps(user,ensure_ascii=False)}], 'format':schema.model_json_schema(),'stream':False,'think':False,'options':{'temperature':0,'num_ctx':12288,'num_predict':1800}}
 try:
  with httpx.Client(timeout=httpx.Timeout(120,connect=5),trust_env=False) as client:
   r=client.post(endpoint()+'/api/chat',json=payload);r.raise_for_status();raw=r.json()
  obj=schema.model_validate_json(raw['message']['content'])
  return obj,{'model':raw.get('model',payload['model']),'eval_count':raw.get('eval_count'),'total_duration_ns':raw.get('total_duration'),'source':'LOCAL_OLLAMA_RESPONSE'}
 except Exception as e:raise ModelFailure('Local model failed or returned invalid structured output: '+str(e)[:500]) from e

def plan_search(event):
 system=(ROOT/'prompts/search_planner.txt').read_text()
 obj,meta=call_json(system,{'event':event,'purpose':'Create document-search queries, not a diagnosis or flight decision.'},SearchPlan)
 return obj.queries,meta

def explain(evidence):
 system=(ROOT/'prompts/recovery_summary.txt').read_text()
 obj,meta=call_json(system,evidence,ModelExplanation)
 available=set(evidence['allowed_evidence_ids'])
 for claim in obj.claims:
  if not set(claim.evidence_ids)<=available:raise ModelFailure('Model cited evidence that was not supplied.')
 # Text remains a human-review draft. Valid citation identifiers do not prove a claim.
 return obj.model_dump(),meta

def embed(texts,model=None):
 model=model or os.getenv('EMBEDDING_MODEL','nomic-embed-text')
 if 'cloud' in model.lower():raise ModelFailure('Cloud embedding model forbidden.')
 try:
  with httpx.Client(timeout=120,trust_env=False) as client:
   r=client.post(endpoint()+'/api/embed',json={'model':model,'input':texts,'truncate':False});r.raise_for_status();v=r.json()['embeddings']
  if len(v)!=len(texts) or not all(isinstance(x,list) and len(x)>0 for x in v):raise ValueError('Invalid embedding batch')
  return v
 except Exception as e:raise ModelFailure('Local embedding failed: '+str(e)[:300]) from e
