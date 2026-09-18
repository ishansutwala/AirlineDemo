from __future__ import annotations
import json,math,re,hashlib
from .db import fetch

def eligible_chunks(c,operator,aircraft_type,config,station,clock):
 return fetch(c,"""SELECT ch.*,d.title,d.revision,d.pdf_path,d.doc_type,d.sha256 FROM doc_chunks ch JOIN documents d ON ch.doc_id=d.doc_id
 WHERE d.operator_id=? AND d.aircraft_type IN (?, 'ALL') AND d.config_code IN (?, 'ALL') AND d.station IN (?, 'ALL')
 AND d.status='ACTIVE' AND d.trust_status='TRUSTED' AND d.valid_from<=? AND d.valid_to>? ORDER BY ch.chunk_id""",(operator,aircraft_type,config,station,clock,clock))
def corpus_hash(c):return hashlib.sha256(''.join(x['chunk_id']+x['content'] for x in fetch(c,'SELECT chunk_id,content FROM doc_chunks ORDER BY chunk_id')).encode()).hexdigest()
def cosine(a,b):
 if len(a)!=len(b) or not a:return 0.0
 den=math.sqrt(sum(x*x for x in a))*math.sqrt(sum(x*x for x in b))
 return sum(x*y for x,y in zip(a,b))/den if den else 0.0

def search(c,operator,aircraft_type,config,station,clock,query,limit=14,query_vector=None,embedding_model=None):
 allowed={x['chunk_id']:x for x in eligible_chunks(c,operator,aircraft_type,config,station,clock)}
 tokens=re.findall(r'[A-Za-z0-9]{2,}',query)[:20]
 expression=' OR '.join('"'+t+'"' for t in tokens) or '"cabin"'
 # Authorization/applicability filtering is applied before exposing or ranking any result.
 ranked=fetch(c,'SELECT chunk_id,bm25(chunks_fts) AS score FROM chunks_fts WHERE chunks_fts MATCH ? ORDER BY score',(expression,))
 lexical=[x['chunk_id'] for x in ranked if x['chunk_id'] in allowed]
 scores={cid:1/(60+i) for i,cid in enumerate(lexical,1)};mode='LEXICAL_FTS5_WITH_METADATA'
 if query_vector is not None and embedding_model:
  chash=corpus_hash(c)
  semantic=[]
  for row in fetch(c,'SELECT * FROM embeddings WHERE model=? AND corpus_hash=?',(embedding_model,chash)):
   if row['chunk_id'] in allowed:semantic.append((cosine(query_vector,json.loads(row['vector_json'])),row['chunk_id']))
  if semantic:
   for i,(_,cid) in enumerate(sorted(semantic,reverse=True),1):scores[cid]=scores.get(cid,0)+1/(60+i)
   mode='HYBRID_FTS5_LOCAL_EMBEDDING_RRF'
 selected=[allowed[cid] for cid in sorted(scores,key=lambda k:(-scores[k],k))[:limit]]
 # Required contextual scopes cannot be displaced by semantic similarity.
 for kind in ['PLANNING','DISPATCH_REVIEW','SOP']:
  mandatory=next((x for x in allowed.values() if x['doc_type']==kind and x['ordinal']==1),None)
  if mandatory and mandatory['chunk_id'] not in {x['chunk_id'] for x in selected}:selected.append(mandatory)
 return {'mode':mode,'query':query,'chunks':selected,'eligible_doc_types':sorted({x['doc_type'] for x in allowed.values()})}
