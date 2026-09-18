from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.main import app
from app import schemas,db
out=db.ROOT/'schemas';out.mkdir(exist_ok=True)
(out/'openapi.json').write_text(json.dumps(app.openapi(),indent=2)+'\n')
for name in ['Event','Authorization','Analyze','Approve','Update','Advance','Outcome','SearchPlan','ModelExplanation']:
 (out/(name.lower()+'.schema.json')).write_text(json.dumps(getattr(schemas,name).model_json_schema(),indent=2)+'\n')
print('Exported OpenAPI and 9 JSON schemas')
