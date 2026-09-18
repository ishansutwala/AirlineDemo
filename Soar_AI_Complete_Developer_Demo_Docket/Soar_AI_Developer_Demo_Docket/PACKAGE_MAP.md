# Package map

Start with **START_HERE.md**. This map describes the role of each folder; **FILE_MANIFEST.tsv** lists every file and its checksum.

| Location | Contents and developer use |
|---|---|
| docs/ | 19-page PDF and editable DOCX; functional and technical Markdown; 274-field data dictionary; editable Mermaid architecture and entity relationships; structured document content |
| app/ | Runnable FastAPI workflow, deterministic rules, retrieval, local model adapter, role checks, static browser UI, optional read-only MCP wrapper |
| database/ | SQLite schema, ready inspection database and SQLite-specific SQL dump |
| data/seed/ | 23 CSV inputs; regenerate runtime database from these files |
| data/scenarios/ | 12 scenario mutations and expected outcomes |
| data/events/ | Simulated source event, revocation, diversion and external completion payloads |
| data/public/ | Public airport facts and route-pattern snapshot, separated from synthetic operations |
| knowledge/ | 16 original synthetic planning documents in PDF/Markdown; contextual sample emails; intentionally inapplicable/untrusted retrieval tests |
| config/ and prompts/ | Policy thresholds, approval constraints and structured local-model prompts |
| schemas/ | Exported OpenAPI and JSON schemas generated from implemented request/response contracts |
| sources/ | 14-source register, source URLs, usage and evidence limitations |
| examples/ | Ten-frame storyboard, timeline, API request examples, actual reference outputs and UI renders |
| scripts/ | Deterministic generators, database seeding, validation, contract exports, full-flow client, optional local embeddings and model manifest |
| tests/ | Automated implementation checks and model-evaluation prompts |
| qa/ | Executed test evidence, runtime versions and precise validation limitations |
| root configuration | Versioned runtime/development dependencies, launchers and optional container configuration |

The native installation is the tested path. Optional model and deployment components require local installation and validation. A runtime database is created locally; it is intentionally not shipped with used demonstration state.
