# Soar.AI - aircraft recovery before arrival

This is a developer handover and executable local prototype, not operational aviation software. No SLM is installed on an aircraft. All maintenance, inventory, staffing, authorization and outcome records are fictional. No real technical maintenance procedures or airline credentials are included.

## Open these first

1. `docs/Soar_AI_Complete_Developer_Docket.pdf` - functional story, architecture, rules, setup, safety boundaries, sources and runbook. The editable DOCX and Markdown versions are alongside it.
2. `docs/DATA_DICTIONARY.md` - every database field, key, type, example and domain.
3. `examples/nominal_case_export.json` - actual output from the reference-mode HTTP smoke test.
4. `schemas/openapi.json` and `schemas/*.schema.json` - machine-readable contracts exported from the application.
5. `qa/VALIDATION_STATUS.md` - exactly what was executed and what still needs developer validation.

## Run without a model first

Use Python 3.13. All commands run from this extracted folder. Install dependencies before an offline demo.

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python scripts/seed_db.py
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

macOS / Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/seed_db.py
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

Open `http://127.0.0.1:8000`. Do not expose this service publicly.

Choose **SIMULATOR**, **nominal**, **Reference replay - NO AI inference**, then **Load / reset fixture**. Choose **MCC** and **Prepare recovery plan**, inspect the evidence, then **Approve preparation**. Choose **SIMULATOR** again, advance to **08:30 CEST**, arrive at stand at **08:50 CEST**, then record external completion at **09:35 CEST**. The state should end at `CLOSED` with the unused part hold released.

The personas use local sample tokens: `demo-mcc-local`, `demo-occ-local`, `demo-viewer-local`, `demo-simulator-local`. These are not production identity/authentication. Set `DEMO_<ROLE>_TOKEN` on the app process to override, and enter the token in the UI override field. `.env.example` is not automatically loaded by native Python.

## What is already supplied

- 23 CSV seed tables, 1,356 rows; a ready SQLite database and rebuilding scripts.
- 300 historical maintenance records and 300 linked work orders for a selected fictional A350 subfleet.
- 156 flight records, 126 inventory lots, 48 engineers, 48 authorizations, 144 shifts, 36 tools, 5 logistics quotes.
- 16 one-page simulation PDFs plus Markdown originals and 47 indexed section chunks.
- 12 deterministic scenarios and separate revocation/diversion/external-outcome events.
- Public airport references, a published route-pattern snapshot, and 14 cited reference sources.
- A reference UI and APIs, optional local Ollama inference, optional local embeddings, an optional read-only MCP adapter, and tests.

## Use actual local SLM inference

Install Ollama separately. Configure `OLLAMA_NO_CLOUD=1` on the **Ollama server process**, then restart that server. Pull `qwen3:8b` during setup. Set the app's `OLLAMA_BASE_URL=http://127.0.0.1:11434` and `OLLAMA_MODEL=qwen3:8b`; select **Live local SLM** in the UI. The app calls the actual local model for search planning and a cited draft briefing. It does not silently replay a reference result if the model fails.

For optional semantic retrieval, pull `nomic-embed-text`, load the intended scenario, run `python scripts/build_embeddings.py`, and enable `ENABLE_SEMANTIC=1` on the app process before analysis. A scenario reset removes the index: rebuild afterward. FTS5 keyword retrieval still works without it. The app reports the retrieval mode actually used.

Record the installed model digest/runtime with `python scripts/model_manifest.py`. Model weights, GPU performance and live inference were not validated in this delivery environment. See the dedicated model setup and QA notes before presenting this as live AI.

## Validate / inspect

Run these from the activated environment, or substitute the platform-specific virtual-environment Python path:

```bash
python -m pytest -q
python scripts/validate_data.py
python scripts/export_contracts.py
python scripts/run_nominal.py --mode reference
```

The last command requires the server to be running and **resets the local demonstration database**. It writes a complete evidence export. Use `--mode ollama` for a real local-model run after setup; note that its reset also removes any optional semantic index.

## Data editing / regeneration

`data/seed/*.csv` are the import inputs. `database/schema.sql` is SQLite DDL. `python scripts/generate_data.py` recreates the deterministic fixture inputs and Markdown documents; `python scripts/seed_db.py` creates the runtime database. `scripts/render_knowledge.py` rebuilds the one-page PDF fixtures after a source edit (requires `requirements-authoring.txt`). The packaged `database/seed.sqlite` is an inspection snapshot, not automatically used as runtime storage.

To rebuild the packaged inspection database and all PDF fixtures consistently after editing or generating data:

```bash
python scripts/generate_data.py
python scripts/seed_db.py --path database/seed.sqlite
python scripts/render_knowledge.py
python scripts/seed_db.py
python scripts/validate_data.py
python scripts/export_contracts.py
```

`generate_data.py` overwrites fixture inputs; skip it when preserving manual CSV edits. `render_knowledge.py` reads the inspection database, so rebuild that database first. Re-export the SQLite dump after changes when needed:

```bash
python -c "import sqlite3,pathlib; c=sqlite3.connect('database/seed.sqlite'); pathlib.Path('database/seed_dump.sqlite.sql').write_text('\n'.join(c.iterdump()),encoding='utf-8')"
```

Edit `docs/docket_content.json` and run `python scripts/render_docket.py` to rebuild the DOCX. Export that DOCX to PDF with an installed office application and review the output. `docs/DEVELOPER_DOCKET.md` is the readable text copy; keep it aligned after document edits.

Never use `seed_dump.sqlite.sql` as a PostgreSQL migration. The dump is a SQLite inspection/export artifact with FTS internals. The tested restoration path is `seed_db.py`.

## Optional integrations

`python -m app.mcp_readonly` supplies a read-only stdio MCP wrapper after installing an organization-approved official SDK via `requirements-mcp.txt`. It is not used by the reference UI and was not executed here. Docker files are supplied but not runtime-tested here. Native Python is the validated path.

## Important behavior

A350 event code `DEMO-A350-21-047` is fictional. The Frankfurt unit is physically present but quarantined. The AMS part reaches FRA at 12:20 CEST in the simulated quote, too late for the 11:00 departure. The agent is not allowed to create a MEL approval. The assumed local-resolution branch has no modeled departure delay; that does not prove saved ground minutes or additional flying hours.

No email, shipment booking, aircraft swap, cockpit message or operational maintenance release is sent. The hash-linked local audit is not an immutable regulatory archive. Disable reset and simulator endpoints, replace local tokens, and perform airline/IT/safety review before considering any real integration.
