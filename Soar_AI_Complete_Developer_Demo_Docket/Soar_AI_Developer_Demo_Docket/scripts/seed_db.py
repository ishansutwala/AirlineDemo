from pathlib import Path
import argparse,sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.db import ROOT,seed_database,connect,SEED_ORDER
p=argparse.ArgumentParser();p.add_argument('--path',default=str(ROOT/'runtime/demo.sqlite'));p.add_argument('--scenario',default='nominal');a=p.parse_args()
seed_database(a.path,a.scenario)
with connect(a.path) as c:counts={t:c.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in SEED_ORDER}
print(json.dumps({'database':a.path,'scenario':a.scenario,'seed_rows':sum(counts.values()),'tables':counts},indent=2))
