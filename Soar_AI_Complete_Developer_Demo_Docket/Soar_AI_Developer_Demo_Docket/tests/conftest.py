import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app.main import app
from app.db import seed_database
@pytest.fixture
def client(tmp_path,monkeypatch):
 path=tmp_path/'test.sqlite';monkeypatch.setenv('DEMO_DB_PATH',str(path));seed_database(path)
 with TestClient(app) as c:yield c
@pytest.fixture
def h():return {r:{'Authorization':f'Bearer demo-{r.lower()}-local'} for r in ['MCC','OCC','VIEWER','SIMULATOR']}
