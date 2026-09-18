# Aircraft recovery before arrival

Complete developer demo docket | Version 1.0 | 14 September 2026

Build a ground-based, private AI workspace that receives an aircraft maintenance event while the aircraft is airborne, assembles the ground team's evidence and resources, and presents preparation options for human approval. No SLM is installed onboard. No AI action changes aircraft systems or makes a flight-safety, dispatch or maintenance-release decision.

## What is in the package

A runnable FastAPI application and offline web interface; a prebuilt SQLite database; SQL schema and seed exports; 23 CSV seed tables; 16 fictional knowledge documents in PDF and Markdown; 47 retrieval chunks; 12 scenarios; source references; JSON schemas and OpenAPI; local-model prompts and adapters; automated tests; and a presenter runbook.

## Two explicitly different execution modes

REFERENCE runs a deterministic, repeatable workflow without model inference. Use it to establish data, rules and UI behavior. LIVE LOCAL SLM calls a separately installed Ollama model to formulate searches and draft an evidence-cited briefing. The same deterministic rules and approval gate remain in control. The screen must never present reference replay as a live AI result.

> All airline operational records, fault codes, parts, authorizations, documents, logistics quotes and outcomes are fictional. The public route and airport reference facts are separately identified. This is not an OEM manual, an approved airline procedure, a real Emirates incident or a production-ready aviation system.

## Start here

Extract the ZIP; open START_HERE.md; run the reference workflow; review examples/nominal_case_export.json; then configure the local model and execute the evaluation checklist. This PDF explains the decisions and expected behavior. The source files and machine-readable contracts are the implementation authority.

# Scenario, people and time conventions

Simulation Airways (SIM-AIR) operates fictional aircraft AC-001, display tail A6-SLM, A350-900 configuration CAB-C01. SIM043/SIM044 use the publicly listed EK43/EK44 route and time pattern as an anchor. Emirates lists Airbus 350 on that route page; no actual same-tail allocation or dated incident is asserted. [S02]

| Moment on 14 September | UTC stored in data | Frankfurt display |
| --- | --- | --- |
| Ground event received | 06:05:05Z | 08:05:05 CEST |
| MCC preparation permission issued | 06:06:00Z | 08:06 CEST |
| Initial case / analysis clock | 06:15:00Z | 08:15 CEST |
| Pre-arrival demonstration moment | 06:30:00Z | 08:30 CEST |
| Estimated touchdown (assumption) | 06:40:00Z | 08:40 CEST |
| Arrival at stand / in-block | 06:50:00Z | 08:50 CEST |
| Illustrative physical work completed | 07:35:00Z | 09:35 CEST |
| Next scheduled off-block departure | 09:00:00Z | 11:00 CEST |

The scheduled stand-to-departure window is 130 minutes. Touchdown and arrival at stand are deliberately distinct; the ten-minute taxi assumption is synthetic. At 08:30 the aircraft is still airborne, ten minutes from the assumed touchdown and twenty minutes from stand arrival. The application stores UTC with a Z suffix; Frankfurt uses Europe/Berlin and Dubai Asia/Dubai. [S14]

## The event is a symptom, not a diagnosis

DEMO-A350-21-047 represents an intermittent cabin-zone temperature indication. It is an invented maintenance event, not an Airbus ECAM code. A similar recorded symptom 42 days earlier is useful context, not proof of the same root cause. Crew operational status and ground-preparation permission are supplied by the simulated airline source, never inferred by the SLM.

# Frame-by-frame story: event to evidence

| Frame | What to show and do | Expected behavior / presenter line |
| --- | --- | --- |
| 1. Establish the rotation | Open the workspace. Show DXB-FRA-DXB and the 11:00 next departure. Explain that the airline and incident are fictional. | "We are preparing the ground response, not controlling this aircraft." |
| 2. Receive an airborne event | As SIMULATOR, load nominal. Show the event timestamp, destination, source and reported symptom. | Case CREATED. The physical fault has not been diagnosed by the model. |
| 3. Apply the authority boundary | Inspect the supplied authorization: ENABLED, GROUND_PREPARATION_ONLY, expires 07:00Z. | "Maintenance Control permits preparation. Flight safety stays outside this workspace." |
| 4. Assemble relevant evidence | Select MCC and run Prepare recovery plan. Reference mode is visibly marked; live mode performs the configured local model calls. | History includes HIST-0042. Retrieve applicable current documents; exclude wrong type, configuration, tenant, future and untrusted content. |
| 5. Check the ground resources | Show FRA physical stock 1 but usable stock 0; AMS usable 1; eligible FRA engineer and tool; expired and wrong-type alternatives. | "A database count is not the same as an available, usable component or an authorized person." |

The supplied UI is a single operations workspace, not ten separate pages or a cinematic animation. These frames are the presenter's sequence across that workspace. The tool list is a record of completed bounded reads, not a fabricated stream of autonomous thought.

# Frame-by-frame story: choice to completion

| Frame | What to show and do | Expected behavior / presenter line |
| --- | --- | --- |
| 6. Compare options | Show A: conditional local resolution. B: dispatch-review evidence only. C: component movement contingency. D: no uncommitted compatible spare. | A meets the illustrative schedule if its physical assumptions hold. C does not: AMS part ready at FRA 12:20 CEST. B is never a flight permission. |
| 7. Approve preparation | As MCC, click Approve preparation before the plan expires. | One approval, one reversible component hold, and three simulated outbox records. No real notification, shipment or work-order integration occurs. |
| 8. Aircraft remains airborne | Switch to SIMULATOR; advance to 08:30 CEST. Show AIRBORNE, 20 minutes to stand, prepared evidence and held contingency. | "The aircraft has not arrived, but the ground team has its preparation package." |
| 9. Arrive and validate physically | As SIMULATOR, click Arrive at stand: 08:50 CEST. | State ON_STAND. Authorized personnel perform physical work outside this application. No actual procedure is generated here. |
| 10. Record the external outcome | As SIMULATOR, record external completion at 09:35 CEST; export evidence JSON. | State CLOSED; unused hold released. Status came from an external-system fixture, not from the model. |

## Do not claim an unmeasured benefit

The nominal scenario demonstrates pre-arrival information assembly and preparation. It does not measure airline ground-time savings or additional flight hours. Existing aircraft-health platforms already support pre-arrival maintenance activities. Any incremental benefit must be measured against the airline's actual existing workflow, not an invented baseline where every team waits until landing. [S01]

# Architecture and trust boundaries

```text
AIRCRAFT: existing systems + flight crew
    | existing aircraft/airline event communication
    v
GROUND: OEM/airline health platform + MCC
    | trusted adapter supplies preparation authorization
    v
PRIVATE AIRLINE ENVIRONMENT
  Intake validation -> bounded recovery workflow
       | local SLM: search planning + cited briefing
       | retrieval: current authorized knowledge
       | APIs/SQL adapters: history, parts, staff, flights
       | rules: eligibility, timing, options, permissions
    v
HUMAN: review -> APPROVE PREPARATION
    | validated, reversible demo writes only
    v
DRAFT WORK PACKAGE / SIMULATED OUTBOX / PART HOLD

No return path to flight controls or cockpit decisions.
```

The starter uses one FastAPI service, SQLite with FTS5, static HTML/CSS/JavaScript, and an optional local Ollama endpoint. These are deliberately small deployment boundaries for a demonstration. SQLite tables simulate independent airline systems; they do not mean a real airline stores all operations in one database.

The optional MCP wrapper exposes read-only views over the same local REST service. It does not replace server-side permissions and is not invoked by the supplied UI. Production may replace local adapters with AMOS/TRAX/ERP/OCC or OEM interfaces after the airline supplies supported contracts, credentials and licenses. No such integration is included or claimed.

> The ground authorization field is this application's workflow contract, not an aircraft certification standard or a universal aircraft-health field. A real deployment must obtain its value through the airline's approved human/process controls.

# Implementation map and data movement

| File / directory | Responsibility |
| --- | --- |
| app/main.py | REST endpoints, role checks, case versioning, approvals, simulator controls, audit and document downloads. |
| app/schemas.py | Strict event and request validation; structured local-model output schemas. |
| app/engine.py | Bounded evidence assembly and deterministic resource/timing calculations. |
| app/retrieval.py | Operator/type/configuration/effectivity/trust filtering, FTS5 search, optional local-vector rank fusion. |
| app/model.py + prompts/ | Local-only Ollama calls; search planning and cited draft explanations; explicit errors instead of silent replay. |
| app/db.py + database/ | SQLite connection, deterministic seeding, hash-chain audit and SQL schema. |
| app/static/ | Offline operations UI. No map tiles, font service, public model or CDN dependency. |
| scripts/ + tests/ | Rebuild, validate, export contracts, run the scenario, build local embeddings, test constraints. |

## One analysis request

Validate the event and current MCC permission. Resolve the aircraft and rotations. In live mode ask the local model for up to three search phrases. Read applicable evidence, history, stock, authorizations, tooling and transport quotes. Calculate recovery options in Python. In live mode request a schema-constrained briefing with supplied evidence identifiers. Persist the complete plan and its hash, increment the case version, and await approval.

## One approval request

Validate role, case version, plan hash, permission and plan expiry. Recompute resource constraints inside a transaction and check the originally cited documents remain applicable. Create a single idempotent approval and, where available, a reversible stock hold. Store three simulated outbox items. Nothing sends email, books a courier or releases an aircraft.

# Database and file inventory

| Dataset group | Rows | Purpose |
| --- | --- | --- |
| airports / sources | 12 / 14 | Public airport facts and source register |
| operators / aircraft | 2 / 12 | Fictional operators and mixed-fleet masters |
| parts / part_effectivity | 16 / 16 | Catalog, configuration applicability and validity |
| fault_catalog / task_requirements | 6 / 6 | Fictional symptom families and planning durations |
| providers / inventory_lots | 24 / 126 | MRO/logistics placeholders and inventory states |
| engineers / authorizations / shifts | 48 / 48 / 144 | Named demo resources, validity and work windows |
| tool_assets | 36 | Serviceability, calibration and availability |
| flights / fleet_status | 156 / 11 | Seven-day rotations and allocated/inbound tails |
| defects / work_orders | 300 / 300 | Historical cases and linked work records |
| open_deferrals / logistics_quotes | 6 / 5 | Review dependencies and synthetic movement quotes |
| communications | 5 | Four contextual messages plus an untrusted test |
| documents / doc_chunks | 16 / 47 | PDF/Markdown metadata and stable section chunks |

Total: 23 seed tables and 1,356 seed rows, excluding empty runtime tables and the derived FTS index. The database also includes cases, approvals, reservations, outbox, audit and optional embeddings. All table columns, keys, types, nullability and domains are described in docs/DATA_DICTIONARY.md and data/data_dictionary.csv.

database/seed.sqlite is ready to inspect. Rebuild through scripts/seed_db.py, which applies schema.sql and imports data/seed/*.csv in foreign-key order. The SQL dump is SQLite-specific; this is not a tested PostgreSQL migration.

# Realism, provenance and data editing

## Public reference versus fictional operation

data/public/airports_reference.csv contains identifiers, names and coordinates transcribed from the linked OurAirports airport pages. OurAirports describes its data as public domain and without an accuracy guarantee; the coordinates are illustrative and not for navigation. Time-zone identifiers were explicitly assigned for application display. [S04]

data/public/route_reference.json preserves the published EK43/EK44 route-page snapshot and its source. Every application flight is still labelled synthetic because tail allocation, operating day and recovery assumptions are not verified airline records. No full airline, OEM or regulatory document is redistributed. [S02]

## Curated complexity, rather than arbitrary large files

The hero inventory includes quarantined FRA stock, serviceable pooled AMS stock, spare CDG/DXB stock and unusable VIE/LHR alternatives. Historical cases cover a selected A350 CAB-C01 subfleet. Other aircraft, configurations and tenants provide distractors. Staff records distinguish aircraft familiarity from a valid operator/task authorization. A parked or inbound aircraft is not treated as a free spare.

## Safe ways to change the story

For a new scenario, copy a JSON file in data/scenarios, patch the event or apply whitelisted row overrides, then reseed and rerun tests. For a new master record, preserve primary/foreign keys and edit the CSV or generator. For a document edit, update its metadata, chunks, Markdown hash and PDF together. Regenerate the FTS and optional embeddings; never silently reuse an index from a different corpus.

> A scenario load deletes and recreates the isolated demo database. It is intentionally destructive and single-user. Never point this application at a production database, real inventory or an operational airline account.

# Knowledge, retrieval and citation behavior

The included knowledge documents are original planning fixtures, not copies of an AMM, TSM/FIM or operator MEL. They describe information and resource preparation without reset instructions, measurements, wiring, troubleshooting actions or flight restrictions. SIM-MEL-21-R2 is explicitly a review checklist and supplies no dispatch permission.

## Eligibility before similarity

Only current ACTIVE, TRUSTED documents matching operator, aircraft type, configuration and station (or ALL where allowed) can enter the prompt. valid_from is inclusive and valid_to exclusive. Relevant retired, future-effective, wrong-type, wrong-configuration and other-operator documents are seeded to test this exclusion. An untrusted document contains an intentional instruction-injection canary and must not appear in retrieval output.

## Baseline and optional semantic path

The default uses SQLite FTS5 keyword search and metadata filters. It is not represented as semantic RAG. ENABLE_SEMANTIC=1 adds locally generated embeddings and reciprocal-rank fusion only if an index exists for the configured embedding model and current corpus hash. The returned retrieval_mode records which path actually ran. Index all 47 chunks locally, but filter access and applicability before exposing results.

## Evidence contract

Each returned chunk includes a stable chunk_id, doc_id, revision, section, page and Markdown-content hash. The supplied PDFs are one-page fixtures so page=1 is exact. Model claims must reference identifiers supplied in the evidence envelope. Identifier validation prevents fabricated references but does not establish that the prose is true: a human reviewer must verify claim-to-evidence meaning. [S06]

Required PLANNING and DISPATCH_REVIEW evidence is checked independently of search ranking. Current relevant evidence cannot be displaced merely because another text has a higher semantic score. Missing required evidence blocks approval instead of producing an invented technical answer.

# Deterministic rules and option calculations

## Stock, people and tools

Usable stock requires a matching part/configuration/operator effectivity record, SERVICEABLE condition, VERIFIED release-document status, unexpired lot, permitted ownership/pooling, current snapshot and unreserved quantity. Staff require the correct operator, type, configuration, task, station, validity and full shift window. Tools require serviceability, current calibration and a usable availability window. Thirty-minute snapshot limits are fixture policy, not an aviation standard.

## Option A: conditional local resolution

```text
Start = max(in-block + 5 min, engineer free, tool free)
      = 06:55Z
Work = 15 inspection + 10 resolution + 10 verification
       + 5 recording = 40 min
Maintenance ready = 07:35Z
Departure = max(scheduled out,
  max(maintenance ready, other-turnaround ready) + 20 min)
          = max(09:00Z, max(07:35Z,08:40Z)+20 min)
          = 09:00Z; simulated delay = 0 min
```

## Option C: feasible contingency, but late

At 06:15Z the AMS item can be staged by 06:45Z, before the synthetic 07:10Z tender cutoff. The quote departs 08:10Z, arrives 09:20Z and requires 60 minutes destination handling. Part available at FRA: 10:20Z (12:20 CEST). A 75-minute complete replacement work package plus the 20-minute departure buffer yields 11:55Z (13:55 CEST), 175 minutes after schedule. Every duration and quote is an assumption, not an airline benchmark.

Option B provides an evidence checklist only: dispatch_eligibility remains UNKNOWN and no departure time is calculated. Option D reports no uncommitted compatible spare. The model cannot overwrite these calculated fields. Crew/slot flags and broader network constraints require a separate authorized OCC review, not an SLM conclusion.

# API contracts, identities and approvals

| Action | HTTP endpoint suffix | Authorized persona |
| --- | --- | --- |
| Load/reset a scenario | POST /api/demo/load | SIMULATOR |
| Receive an event | POST /api/events | SIMULATOR |
| Read a case | GET /api/cases/{id} | Any demo persona |
| Prepare the plan | POST /api/cases/{id}/analyze | MCC |
| Approve preparation | POST /api/cases/{id}/approve-preparation | MCC |
| Revoke / report changed operation | POST /api/cases/{id}/update | SIMULATOR |
| Advance / record external result | POST .../advance-clock; .../external-outcome | SIMULATOR |
| Export the evidence/audit | GET /api/cases/{id}/export | Any demo persona |

schemas/openapi.json is exported from the application, not separately handwritten. Nine JSON schemas describe the event, authorization, requests and model response. Unknown request fields are rejected. Model output cannot include a new dispatch status because its schema restricts that field to UNKNOWN. Source event IDs and increasing sequence numbers support deduplication and invalidation.

## Approval payload

```text
{
  "case_version": <version returned by analysis>,
  "plan_hash": "<64-character returned SHA-256>",
  "idempotency_key": "<new stable request identifier>"
}
```

A duplicate effective approval returns the existing result without creating a second hold or message. A revoked or version-invalidated approval cannot be replayed as a new action. HTTP 401 means missing/invalid local token; 403 wrong persona; 409 stale state, hash, time or resource conflict; 422 invalid payload/time; 503 explicit local model failure. No silent change from live inference to reference replay is made.

# States, failure cases and recovery handling

```text
CREATED -> AWAITING_APPROVAL -> PREPARATION_APPROVED
                     |                  |
                human gate         external arrival
                                        v
                                    ON_STAND
                                        | external completion
                                        v
                                      CLOSED

Authority failure -> BLOCKED
Missing essential evidence -> BLOCKED_EVIDENCE
Local inference error -> MODEL_ERROR
Changed event/destination/permission -> SUSPENDED
```

| Scenario fixture | Expected behavior |
| --- | --- |
| nominal | Prepare A/B and a reversible AMS contingency; no dispatch approval. |
| no_authorization / critical_event / expired_authorization | Block planning using the external flags/permission; no model safety classification. |
| no_engineer / no_tool / missing_current_document / unknown_fault | BLOCKED_EVIDENCE; no approval. |
| stale_inventory | Reject stale AMS inventory and compare the CDG contingency. |
| late_cutoff | Reject AMS air quote when tender cutoff cannot be met. |
| busy_engineer | Option A moves onto the critical path; illustrative delay becomes 60 minutes. |
| no_serviceable_parts | No invented part contingency; retain conditional inspection preparation. |

A newer diversion or permission-revocation message invalidates the current plan and releases its holds. The narrow starter does not calculate a fresh Vienna recovery; a real adapter would first update the rotation, local resources and authorization, then create a new ground case. An active flight-safety event blocks this demo branch even though an airline could separately authorize non-flight ground support during emergencies.

# Install and run the reference demonstration

Use Python 3.13 in an isolated environment. SQLite must include FTS5. The supplied browser UI uses no external assets. Package dependencies need to be installed before going offline; model files are optional for reference mode. Run from the extracted package directory.

## Windows PowerShell

```text
py -3.13 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python scripts/seed_db.py
.\.venv\Scripts\python -m uvicorn app.main:app --port 8000
```

## macOS / Linux

```text
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/seed_db.py
.venv/bin/python -m uvicorn app.main:app --port 8000
```

Open http://127.0.0.1:8000. Choose SIMULATOR, nominal, Reference replay and Load / reset fixture. Switch to MCC to prepare and approve. Switch back to SIMULATOR to advance time and record the external result. Changing the persona changes the local sample bearer token; the optional token field supports environment overrides.

## Automated reference run

```text
python scripts/run_nominal.py --mode reference
python -m pytest -q
python scripts/validate_data.py
```

start_demo.sh and start_demo.ps1 are convenience launchers. .env.example is documentation: native Python does not automatically load it. Export variables in the shell; do not assume editing that file changes the process. Dockerfile and compose.yaml are optional deployment scaffolds; the delivered validation used native Python, not Docker.

# Enable the actual private SLM

The supplied candidate is qwen3:8b through Ollama. It is a general open-weight model, not an aviation-trained or certified model. The upstream Qwen3-8B model card lists Apache-2.0; review the actual installed artifact and all component licenses. No model weights are bundled. [S10, S11]

## Prepare and record the local runtime

```text
# Configure the OLLAMA SERVER process, then restart it:
OLLAMA_NO_CLOUD=1

# One-time downloads before an offline presentation:
ollama pull qwen3:8b
ollama pull nomic-embed-text  # optional semantic retrieval

# Application process environment:
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:8b
ENABLE_SEMANTIC=0

python scripts/model_manifest.py
```

Use export NAME=value on macOS/Linux or $env:NAME="value" in PowerShell. OLLAMA_NO_CLOUD must apply to the Ollama server itself; setting it only on FastAPI does not reconfigure an already-running server. Endpoint allowlists and that flag do not replace network egress controls or proof of data residency. [S09]

## Semantic retrieval is optional and order-sensitive

Load the intended scenario first, then run python scripts/build_embeddings.py. Enable ENABLE_SEMANTIC=1 on the application process and select Live local SLM in the UI. A scenario reset deletes the optional index; rebuild it after each reset. Inspect retrieval_mode rather than assuming vectors were used. The reference path remains lexical.

Benchmark the actual model digest, quantization, hardware, prompt and context size. No VRAM, response-time or accuracy guarantee is supplied. Use the included evaluation prompts, inspect citation meaning and test rejected/unknown outputs. The delivery environment did not run a real Ollama model; the adapter contract was tested with mocks and failure tests, not with aircraft-domain model validation.

# Security, sovereignty and aviation boundaries

## Controls actually implemented

Server-side role checks; strict schemas; operator-scoped cases and evidence; local model endpoint allowlist; prompt/data separation; metadata-filtered retrieval; deterministic option fields; plan hashes, versions and expiry; approval-time revalidation; transactional reversible holds; idempotent writes; event-sequence invalidation; a simulated-only outbox; and a local hash-linked audit trail.

## What those controls do not prove

The role selector and sample bearer tokens are demonstration fixtures, not SSO or multi-user identity assurance. Database owners can alter the database or replace the audit file; the hash chain is not an immutable compliance archive. Identifier checks do not prove factual entailment. A localhost model URL alone does not guarantee no data leakage through logs, agents, proxies, plugins or updates. This is not certified software or a safety case.

## Production separation of duty

Use enterprise SSO and short-lived audience-bound tokens, least-privilege service accounts, network isolation, TLS/mTLS as appropriate, secrets management, access-controlled document ingestion, licensed current sources, append-only audit storage, retention controls and an airline-approved incident process. Validate supplier/model licenses and restrict outbound traffic. Remote MCP deployments need their own authorization design; a stdio wrapper is not a secure enterprise gateway. [S13]

## Forbidden scope

No continued-flight or diversion advice; no classification of life-threatening conditions; no release-to-service or airworthiness determination; no MEL dispatch authorization; no cockpit command; no actual movement booking; no automatic aircraft swap. The workflow may prepare a review package only after the supplied ground permission is current. MEL material concerns the authorized dispatch review; it is not a substitute for in-flight crew procedures. [S03]

# Test strategy and acceptance gates

The included automated suite validates the reference workflow, API/role boundaries, eligibility logic, transaction conflicts, evidence exclusion, time-zone arithmetic and failure behavior. qa/test_results.xml and qa/test_output.txt record the executed run. qa/data_validation.json checks database/file consistency. qa/http_smoke_test.json records the full reference scenario against a running local HTTP service.

## Developer definition of done

A new installation runs without editing application source; the seed reconstructs with no foreign-key or integrity errors; the complete nominal flow is reproducible; no denied action is accepted; stale evidence is visibly rejected; only applicable current knowledge is retrieved; quoted logistics and the next departure use the same time basis; reservations are idempotent and reversible; and evidence exports identify the mode actually executed.

## Before calling it a live SLM demo

Install and freeze the model/runtime artifact, then run real inference on the nominal and adversarial fixtures. Verify every claim against its cited evidence; confirm the model never changes deterministic option fields; record context size and elapsed time; remove any unsupported confidence labels; and demonstrate that no external inference endpoint is contacted. Rehearse with venue-network connectivity disabled after setup. A mocked structured response is not live-model validation.

## Before an airline pilot deployment

Replace all synthetic knowledge and data only with authorized licensed sources; integrate supported read APIs; define current-data freshness contracts; obtain maintenance and operational safety review; establish human authority and escalation procedures; evaluate hallucination and abstention rates; add durable workflow execution, real identity, observability, disaster recovery and load tests. Conduct a shadow-mode evaluation before enabling any reversible write integration.

> This handover supplies a tested local reference implementation plus live-model integration code. It does not supply trained model weights, credentials, OEM connectors, an approved MEL, a validated airline knowledge base or an operational release mechanism.

# Runbook, troubleshooting and handover tasks

| Symptom | Check / action |
| --- | --- |
| 401 or 403 | Use the intended persona/token. SIMULATOR ingests/resets/advances; MCC prepares/approves. Tokens changed in environment must also be supplied in the UI override. |
| 409 at approval | Do not retry a stale hash. Check plan TTL, permission, changed resources, newer event and existing approval. Reload the fixture for a clean demonstration. |
| 503 in live mode | Verify local Ollama is running, model exists, schema output is valid and endpoint is allowlisted. The app does not silently switch to replay. |
| Semantic retrieval not shown | Load first, build embeddings for this DB/model/corpus, then analyze. Resetting a scenario removes embeddings. Check ENABLE_SEMANTIC on the app process. |
| No current documents / PDF missing | Run seeding and data validation; verify metadata, hashes and knowledge/pdf paths. Do not work around an applicability failure by removing the filter. |
| Port occupied / multiple presenters | Select another port or stop the other demo. Use one process/worker and an isolated runtime DB per presenter; reset is not multi-user safe. |
| Docker cannot see host model | Host Ollama normally binds locally. Native setup is the tested recommended path. Any container-accessible binding requires explicit private networking/firewall review. |

## Suggested implementation order

First run the reference workflow and inspect its expected export. Next review the data dictionary and source/provenance boundary. Then enable the local SLM, add the optional index and evaluate outputs. Finally refine presentation/UI transitions without changing control semantics. Replace mock adapters only after an airline partner defines access and safety responsibilities.

All fixture changes should be followed by reseeding, contract export, tests and evidence review. Keep public-source facts separate from the scenario assumptions; do not relabel simulation records as an airline case study. Preserve the model manifest and QA results with the exact package version presented.

# Source register and evidence limits

Checked 14 September 2026. The package includes original summaries and small factual reference fields, not copies of full source publications. These sources support context and integration design; none validates the fictional maintenance result or quantifies this prototype's benefit.

## S01 | Airbus - In-flight health monitoring

Existing pre-arrival maintenance preparation workflow; original paraphrase only. Not a source of airline-specific faults, timings, spares or approved maintenance procedures.

https://www.aircraft.airbus.com/en/newsroom/news/2022-07-in-flight-health-monitoring

## S02 | Emirates - Dubai-Frankfurt flight schedules

Public route and schedule snapshot: EK43 03:25 DXB / 08:50 FRA; EK44 11:00 FRA / 19:20 DXB; Airbus 350. Date-dependent schedule; same-tail assignment and all incident details are simulated; no endorsement.

https://www.emirates.com/de/english/destinations/dxb/fra/flights-from-dubai-to-frankfurt/

## S03 | Airbus Safety First - A Recall on the Correct Use of the MEL

General MEL/dispatch boundary and authorized review; no copied procedures. Not the operator MEL; does not authorize dispatch of this fictional defect.

https://safetyfirst.airbus.com/a-recall-on-the-correct-use-of-the-mel/

## S04 | OurAirports - OurAirports open data

Public-domain airport identifiers, names and coordinates transcribed from linked airport pages. Community-maintained reference; no guarantee of accuracy; not for navigation. Bulk CSV download was not used.

https://ourairports.com/data/

## S05 | IATA - Four Priorities to Strengthen the Aviation Supply Chain

Problem framing: visibility and integration of maintenance and material information. Industry-level evidence, not a quantified benefit estimate for this demo.

https://www.iata.org/en/pressroom/2026-releases/06-24-iata-outlines-four-priorities-to-strengthen-aviation-supply-chain/

## S06 | Ollama - Structured Outputs

Local structured JSON response API design. Schema validity is not factual or aviation-safety validity.

https://docs.ollama.com/capabilities/structured-outputs

## S07 | Ollama - Tool calling

Optional model tool-selection implementation reference. This reference build uses a bounded workflow and schema-constrained search planning, not unrestricted autonomous tools.

https://docs.ollama.com/capabilities/tool-calling

# Technical references and distribution notes

## S08 | Ollama - Generate embeddings

Optional local semantic retrieval adapter. Embedding model weights are not bundled; live inference requires local installation.

https://docs.ollama.com/api/embed

## S09 | Ollama - FAQ / local-only cloud settings

Local inference and OLLAMA_NO_CLOUD=1 deployment setting. Setting alone is not proof of sovereignty: also control egress, credentials, logs and updates.

https://docs.ollama.com/faq

## S10 | Qwen - Qwen3-8B model card

Candidate open-weight general model; model card lists Apache-2.0. Not aviation-certified or validated for this task; no weights bundled; evaluate installed artifact.

https://huggingface.co/Qwen/Qwen3-8B

## S11 | Ollama - qwen3:8b model library entry

Concrete optional local model tag. Tags can change; record local model digest and runtime version before presentation.

https://ollama.com/library/qwen3:8b

## S12 | Model Context Protocol - Build an MCP server

Optional read-only stdio adapter design. Remote enterprise MCP authentication and production gateway are not provided by the local stdio adapter.

https://modelcontextprotocol.io/docs/develop/build-server

## S13 | Model Context Protocol - Authorization security considerations

Production authorization considerations and token audience isolation. Use the enterprise-approved supported specification and SDK versions at deployment.

https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations

## S14 | Python - zoneinfo: IANA time zone support

UTC storage, timezone-aware local display. tzdata package may be needed on Windows; fixture clock is fixed, not live.

https://docs.python.org/3/library/zoneinfo.html

Airline names and aircraft types identify the public operating-pattern reference only. No logo, endorsement or confidential manual is included. OurAirports reference values are public-domain data with their stated caveat. Model, SDK and framework licenses remain with their respective projects. Original demo code and fixtures may be adapted for this demonstration; complete third-party license review before any redistribution or production deployment.

