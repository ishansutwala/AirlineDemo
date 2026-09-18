# Delivery validation status

Package: Soar.AI aircraft recovery developer demo, 14 September 2026.

## Executed successfully

| Check | Result | Evidence |
|---|---|---|
| Automated API, workflow, rules, permissions and failure suite | 51 tests passed | test_output.txt; test_results.xml |
| Seed database and file validation | 75 checks passed | data_validation.json |
| Full reference flow over actual local HTTP | Passed: load, analyze, approve, advance, arrival, external completion, export | http_smoke_test.json; ../examples/nominal_case_export.json |
| Browser HTML/JS rendering with actual TestClient response objects | Passed; no JavaScript rendering errors | browser_validation.json; ../examples/workspace_*.png |
| JavaScript syntax | `node --check app/static/app.js` passed | Executed during packaging |
| Main handover rendering | 19-page PDF visually reviewed; final DOCX exported and page images inspected | ../docs/Soar_AI_Complete_Developer_Docket.pdf |
| Synthetic knowledge PDFs | 16 single-page PDFs rendered and visually reviewed | ../knowledge/pdf/ |

The browser environment blocks navigation to localhost by administrator policy. No bypass was attempted. The browser check loaded HTML and JavaScript offline and supplied real response objects from the application. It is not a browser-to-server navigation test. Server HTTP behavior was checked separately using HTTPX and a running Uvicorn process.

## Not executed or not supplied

Actual Ollama/Qwen inference, GPU performance, semantic embedding inference, the optional MCP SDK adapter, Docker deployment, Windows/macOS execution, real airline/OEM integration, production identity, penetration tests and aviation operational validation were not performed here. The local model adapter has mocked response and failure tests, not model-quality certification. There are no model weights or installed dependency wheels in this package.

The reference mode is deterministic replay plus real local database/rules execution. It must not be presented as live model inference. In live mode the code calls the configured local Ollama model and fails explicitly rather than silently substituting a reference answer.

## Developer acceptance before presentation

Install dependencies and the desired model on the presentation computer. Run the supplied tests, validate the nominal workflow, record the exact model/runtime digest and test every model claim against its cited evidence. Exercise failure scenarios and confirm that the mode, missing information and suspended authority remain visible. Rehearse with external network access disabled after setup. Record actual model latency and avoid inferred accuracy, time-saving or flying-hour claims.

No flight-safety decision, dispatch authorization, maintenance instruction or operational release is provided by this package. All maintenance/crew/parts records and recovery results are fictional test fixtures. The public route and airport references do not imply an airline incident, endorsement, current tail assignment or a demonstrated benefit.
