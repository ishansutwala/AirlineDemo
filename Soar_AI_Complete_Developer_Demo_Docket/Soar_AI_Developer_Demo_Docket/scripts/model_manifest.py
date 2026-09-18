"""Record the actual installed local runtime/model; does not download or benchmark it."""
from pathlib import Path
import json,sys,platform
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
from app import model,db
with httpx.Client(timeout=30,trust_env=False) as c:
 version=c.get(model.endpoint()+'/api/version');version.raise_for_status()
 tags=c.get(model.endpoint()+'/api/tags');tags.raise_for_status()
manifest={'recorded_at_utc':db.now(),'platform':platform.platform(),'runtime':version.json(),'requested_model':model.model_tag(),'installed_models':tags.json(),'note':'Archive this file for the demo run. A mutable model tag alone is not a reproducibility identifier.'}
p=db.ROOT/'qa/local_model_manifest.json';p.write_text(json.dumps(manifest,indent=2)+'\n');print(p)
