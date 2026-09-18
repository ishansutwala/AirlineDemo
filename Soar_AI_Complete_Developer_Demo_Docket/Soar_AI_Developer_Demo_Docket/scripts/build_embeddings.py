"""Optional local semantic index. Pull the selected embedding model separately first."""
from pathlib import Path
import argparse,json,os,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import db,model,retrieval

def main():
 p=argparse.ArgumentParser();p.add_argument('--database',default=str(db.db_path()));p.add_argument('--model',default=os.getenv('EMBEDDING_MODEL','nomic-embed-text'));a=p.parse_args()
 with db.connect(a.database) as c:
  rows=db.fetch(c,'SELECT chunk_id,section,content FROM doc_chunks ORDER BY chunk_id');chash=retrieval.corpus_hash(c);buffer=[]
  for start in range(0,len(rows),8):
   batch=rows[start:start+8];vectors=model.embed([r['section']+'\n'+r['content'] for r in batch],a.model)
   buffer.extend((r['chunk_id'],a.model,chash,json.dumps(v)) for r,v in zip(batch,vectors))
  c.execute('DELETE FROM embeddings');c.executemany('INSERT INTO embeddings VALUES(?,?,?,?)',buffer)
 print(json.dumps({'indexed_chunks':len(buffer),'model':a.model,'corpus_hash':chash,'note':'Local embedding API executed; no cloud endpoint used by this script.'},indent=2))
if __name__=='__main__':main()
