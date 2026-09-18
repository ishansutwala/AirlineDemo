# Data dictionary

Canonical time contract: `YYYY-MM-DDTHH:MM:SSZ`. Strings compare correctly only in this fixed UTC format; fractional seconds are rejected at API ingestion. CSV empty fields import as NULL. All quantities are counts, durations ending in `_minutes` are minutes, monetary fields ending in `_eur` are synthetic EUR amounts.

The 300 historical records cover the selected A350 CAB-C01 simulation subfleet; they are not a statistical model of an airline. `fleet_status.station` is the destination for an inbound committed tail until `available_from_utc`.

## sources

Provenance register.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| source_id | TEXT required | PK  | Source register reference; not an operational authority. | S01 |
| title | TEXT required |  | Title for provenance register. | In-flight health monitoring |
| publisher | TEXT required |  | Publisher for provenance register. | Airbus |
| url | TEXT required |  | Url for provenance register. | https://www.aircraft.airbus.com/en/newsroom/news/2022-07-in-flight-health-monitoring |
| consulted_on | TEXT required |  | Consulted on for provenance register. | 2026-09-14 |
| usage | TEXT required |  | Usage for provenance register. | Existing pre-arrival maintenance preparation workflow; original paraphrase only. |
| limitations | TEXT required |  | Limitations for provenance register. | Not a source of airline-specific faults, timings, spares or approved maintenance procedures. |

## airports

Public airport references; not navigation data.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| iata | TEXT required | PK  | Iata for public airport references; not navigation data. | AMS |
| icao | TEXT required |  | Icao for public airport references; not navigation data. | OMDB |
| name | TEXT required |  | Name for public airport references; not navigation data. | Dubai International Airport |
| city | TEXT required |  | City for public airport references; not navigation data. | Dubai |
| country | TEXT required |  | Country for public airport references; not navigation data. | AE |
| latitude | REAL required |  | Latitude for public airport references; not navigation data. | 25.24979 |
| longitude | REAL required |  | Longitude for public airport references; not navigation data. | 55.370992 |
| timezone | TEXT required |  | Timezone for public airport references; not navigation data. | Asia/Dubai |
| source_url | TEXT required |  | Source url for public airport references; not navigation data. | https://ourairports.com/airports/OMDB/ |
| data_class | TEXT required |  | Provenance label: distinguish synthetic records from public reference facts. | PUBLIC_REFERENCE |

## operators

Synthetic tenant masters.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| operator_id | TEXT required | PK  | Tenant/operator ownership key; must not be inferred from model prose. | OTHER-AIR |
| name | TEXT required |  | Name for synthetic tenant masters. | Simulation Airways (fictional) |
| home_station | TEXT required | airports.iata | IATA airport/station code; linked master or applicability label. | DXB |
| data_class | TEXT required |  | Provenance label: distinguish synthetic records from public reference facts. | SYNTHETIC |

## aircraft

Fictional mixed-fleet masters.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| aircraft_id | TEXT required | PK  | Internal aircraft identity; used to join history, rotations and cases. | AC-001 |
| operator_id | TEXT required | operators.operator_id | Tenant/operator ownership key; must not be inferred from model prose. | SIM-AIR |
| tail_display | TEXT required |  | Display-only fictional registration; not a verified registered tail. | A6-SLM |
| aircraft_type | TEXT required |  | Aircraft model applicability label. | A350-900 |
| config_code | TEXT required |  | Operator-specific fictional configuration applicability code. | CAB-C01 |
| base_station | TEXT required | airports.iata | IATA airport/station code; linked master or applicability label. | DXB |
| seat_capacity | INTEGER required |  | Seat capacity for fictional mixed-fleet masters. | 312 |
| data_class | TEXT required |  | Provenance label: distinguish synthetic records from public reference facts. | SYNTHETIC |

## parts

Fictional catalog.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| part_id | TEXT required | PK  | Fictional component catalog identifier; not an OEM part number. | DEMO-CZT-100 |
| description | TEXT required |  | Description for fictional catalog. | Cabin zone temperature indication module (fictional part) |
| unit | TEXT required |  | Unit for fictional catalog. | EA |
| reference_cost_eur | REAL required |  | Synthetic reference cost eur value; not a real price or booking. | 3364.73 |
| hazmat | INTEGER required |  | Hazmat for fictional catalog. | 0 |
| data_class | TEXT required |  | Provenance label: distinguish synthetic records from public reference facts. | SYNTHETIC |

## part_effectivity

Allowed component/type/configuration combinations.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| effectivity_id | TEXT required | PK  | Stable effectivity identifier. | EFF-001 |
| part_id | TEXT required | parts.part_id | Fictional component catalog identifier; not an OEM part number. | DEMO-CZT-100 |
| operator_id | TEXT required | operators.operator_id | Tenant/operator ownership key; must not be inferred from model prose. | SIM-AIR |
| aircraft_type | TEXT required |  | Aircraft model applicability label. | A350-900 |
| config_code | TEXT required |  | Operator-specific fictional configuration applicability code. | CAB-C01 |
| valid_from | TEXT required |  | Inclusive beginning of applicability/authorization in canonical UTC. | 2026-01-01T00:00:00Z |
| valid_to | TEXT required |  | Exclusive end of applicability/authorization in canonical UTC. | 2027-01-01T00:00:00Z |
| approval_reference | TEXT required |  | Approval reference for allowed component/type/configuration combinations. | SIM-EFF-001 |
| data_class | TEXT required |  | Provenance label: distinguish synthetic records from public reference facts. | SYNTHETIC |

## fault_catalog

Fictional maintenance symptoms.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| fault_code | TEXT required | PK  | Fictional maintenance-event key; not a real cockpit warning code. | DEMO-25-019 |
| ata_chapter | TEXT required |  | ATA-style topic label for sorting; not a flight-safety classification. | 21 |
| description | TEXT required |  | Description for fictional maintenance symptoms. | Intermittent cabin-zone temperature indication |
| part_id | TEXT required | parts.part_id | Fictional component catalog identifier; not an OEM part number. | DEMO-CZT-100 |
| scope_note | TEXT required |  | Scope note for fictional maintenance symptoms. | Invented event for ground-planning simulation; no real warning mapping or flight-safety classification. |
| data_class | TEXT required |  | Provenance label: distinguish synthetic records from public reference facts. | SYNTHETIC |

## providers

Fictional MRO/logistics contacts.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| provider_id | TEXT required | PK  | Stable provider identifier. | PROV-AMS-LOG |
| station | TEXT required | airports.iata | IATA airport/station code; linked master or applicability label. | DXB |
| name | TEXT required |  | Name for fictional mro/logistics contacts. | Simulation DXB MRO Services |
| contact_email | TEXT required |  | Contact email for fictional mro/logistics contacts. | mro.dxb@example.invalid |
| service_type | TEXT required |  | Service type for fictional mro/logistics contacts. | MRO |
| data_class | TEXT required |  | Provenance label: distinguish synthetic records from public reference facts. | SYNTHETIC |

## inventory_lots

Stock and eligibility evidence.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| lot_id | TEXT required | PK  | Stable lot identifier. | LOT-0001 |
| operator_id | TEXT required | operators.operator_id | Tenant/operator ownership key; must not be inferred from model prose. | SIM-AIR |
| part_id | TEXT required | parts.part_id | Fictional component catalog identifier; not an OEM part number. | DEMO-CZT-100 |
| station | TEXT required | airports.iata | IATA airport/station code; linked master or applicability label. | AMS |
| qty_on_hand | INTEGER required |  | Physical stock count, including stock that may be unusable. | 1 |
| qty_reserved | INTEGER required |  | Quantity already held. Must be between zero and physical count. | 0 |
| condition | TEXT required |  | Serviceability state used independently of physical count. | QUARANTINE / SERVICEABLE / UNSERVICEABLE |
| release_doc_status | TEXT required |  | Fixture indication that release paperwork was verified; not real certificate validation. | MISSING / PENDING / VERIFIED |
| release_doc_id | TEXT nullable |  | Fictional release-paperwork reference. | SIM-REL-LOT-FRA-CZT-Q |
| expiry_utc | TEXT required |  | Expiry utc as canonical UTC timestamp. | 2027-06-30T23:59:59Z |
| owner_type | TEXT required |  | Owner type for stock and eligibility evidence. | OWNED / POOL |
| borrow_approved | INTEGER required |  | 0/1 indication that use of pooled/borrowed stock is authorized in the fixture. | 1 |
| bin_location | TEXT required |  | Bin location for stock and eligibility evidence. | FRA-SIM-A01 |
| last_verified_at | TEXT required |  | Source-snapshot verification time used for freshness checks. | 2026-09-14T06:00:00Z |
| row_version | INTEGER required |  | Optimistic-concurrency marker; increment whenever stock changes. | 1 |
| data_class | TEXT required |  | Provenance label: distinguish synthetic records from public reference facts. | SYNTHETIC |

## engineers

Fictional human resources.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| engineer_id | TEXT required | PK  | Stable engineer identifier. | ENG-AMS-01 |
| name | TEXT required |  | Name for fictional human resources. | Demo Engineer DXB 01 |
| provider_id | TEXT required | providers.provider_id | Stable provider identifier. | PROV-DXB-MRO |
| home_station | TEXT required | airports.iata | IATA airport/station code; linked master or applicability label. | DXB |
| employment_status | TEXT required |  | Employment status for fictional human resources. | ACTIVE |
| data_class | TEXT required |  | Provenance label: distinguish synthetic records from public reference facts. | SYNTHETIC |

## authorizations

Operator/task authority windows.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| authorization_id | TEXT required | PK  | Stable authorization identifier. | AUTH-AMS-01 |
| engineer_id | TEXT required | engineers.engineer_id | Stable engineer identifier. | ENG-DXB-01 |
| operator_id | TEXT required | operators.operator_id | Tenant/operator ownership key; must not be inferred from model prose. | SIM-AIR |
| aircraft_type | TEXT required |  | Aircraft model applicability label. | A320-200 |
| config_code | TEXT required |  | Operator-specific fictional configuration applicability code. | CAB-C01 |
| task_scope | TEXT required |  | Fictional operator/task authorization scope; aircraft type alone is insufficient. | SIM-CABIN-COMFORT |
| station | TEXT required | airports.iata | IATA airport/station code; linked master or applicability label. | AMS |
| valid_from | TEXT required |  | Inclusive beginning of applicability/authorization in canonical UTC. | 2026-01-01T00:00:00Z |
| valid_to | TEXT required |  | Exclusive end of applicability/authorization in canonical UTC. | 2027-06-30T23:59:59Z |
| status | TEXT required |  | Lifecycle/status enum for authorizations; see application rules. | ACTIVE |
| data_class | TEXT required |  | Provenance label: distinguish synthetic records from public reference facts. | SYNTHETIC |

## engineer_shifts

Availability windows.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| shift_id | TEXT required | PK  | Stable shift identifier. | SHIFT-AMS-01-0 |
| engineer_id | TEXT required | engineers.engineer_id | Stable engineer identifier. | ENG-DXB-01 |
| station | TEXT required | airports.iata | IATA airport/station code; linked master or applicability label. | DXB |
| start_utc | TEXT required |  | Start utc as canonical UTC timestamp. | 2026-09-14T05:00:00Z |
| end_utc | TEXT required |  | End utc as canonical UTC timestamp. | 2026-09-14T13:00:00Z |
| busy_until_utc | TEXT required |  | Engineer is committed to other work until this instant. | 2026-09-14T06:45:00Z |
| last_verified_at | TEXT required |  | Source-snapshot verification time used for freshness checks. | 2026-09-14T06:00:00Z |
| data_class | TEXT required |  | Provenance label: distinguish synthetic records from public reference facts. | SYNTHETIC |

## tool_assets

Planning tools and calibration.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| tool_asset_id | TEXT required | PK  | Stable tool asset identifier. | TOOL-AMS-01 |
| station | TEXT required | airports.iata | IATA airport/station code; linked master or applicability label. | DXB |
| tool_code | TEXT required |  | Tool code for planning tools and calibration. | SIM-DIAG-CAB |
| description | TEXT required |  | Description for planning tools and calibration. | Fictional planning resource; consult approved task for actual tooling |
| condition | TEXT required |  | Serviceability state used independently of physical count. | SERVICEABLE |
| calibration_expiry_utc | TEXT required |  | Tool calibration expiry used as a hard planning constraint. | 2027-01-31T23:59:59Z |
| available_from_utc | TEXT required |  | Earliest resource/quote availability; for fleet status, station is an inbound target until this time. | 2026-09-14T06:00:00Z |
| last_verified_at | TEXT required |  | Source-snapshot verification time used for freshness checks. | 2026-09-14T06:00:00Z |
| data_class | TEXT required |  | Provenance label: distinguish synthetic records from public reference facts. | SYNTHETIC |

## task_requirements

Synthetic planning durations, not procedures.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| task_id | TEXT required | PK  | Stable task identifier. | SIM-TASK-001 |
| fault_code | TEXT required | fault_catalog.fault_code | Fictional maintenance-event key; not a real cockpit warning code. | DEMO-A350-21-047 |
| aircraft_type | TEXT required |  | Aircraft model applicability label. | A350-900 |
| config_code | TEXT required |  | Operator-specific fictional configuration applicability code. | CAB-C01 |
| task_scope | TEXT required |  | Fictional operator/task authorization scope; aircraft type alone is insufficient. | SIM-CABIN-COMFORT |
| tool_code | TEXT required |  | Tool code for synthetic planning durations, not procedures. | SIM-DIAG-CAB |
| inspection_minutes | INTEGER required |  | Synthetic inspection minutes planning input. | 15 |
| resolution_minutes | INTEGER required |  | Synthetic resolution minutes planning input. | 10 |
| verification_minutes | INTEGER required |  | Synthetic verification minutes planning input. | 10 |
| recording_minutes | INTEGER required |  | Synthetic recording minutes planning input. | 5 |
| replacement_minutes | INTEGER required |  | Synthetic replacement minutes planning input. | 75 |
| data_class | TEXT required |  | Provenance label: distinguish synthetic records from public reference facts. | SYNTHETIC |

## flights

Public-pattern anchor and synthetic rotations.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| flight_id | TEXT required | PK  | Stable flight identifier. | F-02-0-A |
| operator_id | TEXT required | operators.operator_id | Tenant/operator ownership key; must not be inferred from model prose. | SIM-AIR |
| aircraft_id | TEXT required | aircraft.aircraft_id | Internal aircraft identity; used to join history, rotations and cases. | AC-001 |
| display_number | TEXT required |  | Display number for public-pattern anchor and synthetic rotations. | SIM043 / EK43-pattern |
| origin | TEXT required | airports.iata | IATA airport/station code; linked master or applicability label. | DXB |
| destination | TEXT required | airports.iata | IATA airport/station code; linked master or applicability label. | FRA |
| scheduled_out_utc | TEXT required |  | Scheduled departure/off-block time used to evaluate delay. | 2026-09-13T23:25:00Z |
| scheduled_in_utc | TEXT required |  | Scheduled arrival/in-block time. | 2026-09-14T06:50:00Z |
| estimated_landing_utc | TEXT required |  | Assumed touchdown, distinct from arrival at stand. | 2026-09-14T06:40:00Z |
| estimated_inblock_utc | TEXT required |  | Expected arrival at stand and start of the ground window. | 2026-09-14T06:50:00Z |
| other_turnaround_ready_utc | TEXT required |  | Readiness of parallel non-maintenance activities; do not sum them sequentially. | 2026-09-13T23:05:00Z |
| dispatch_buffer_minutes | INTEGER required |  | Synthetic preparation buffer after all modeled readiness paths; not a dispatch authorization. | 20 |
| passengers | INTEGER required |  | Passengers for public-pattern anchor and synthetic rotations. | 286 |
| crew_ready | INTEGER required |  | Fixture availability flag only; no complete crew-legality calculation is implemented. | 1 |
| slot_confirmed | INTEGER required |  | Fixture slot-status flag only; no ATC/airport-slot integration exists. | 1 |
| status | TEXT required |  | Lifecycle/status enum for flights; see application rules. | AIRBORNE / SCHEDULED |
| source_basis | TEXT required |  | Public-pattern anchor or synthetic-assumption note for a flight. | S02 published route/time anchor; operator/tail allocation simulated |
| data_class | TEXT required |  | Provenance label: distinguish synthetic records from public reference facts. | SYNTHETIC |

## defects

Selected A350 subfleet historical records.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| defect_id | TEXT required | PK  | Stable defect identifier. | HIST-0001 |
| aircraft_id | TEXT required | aircraft.aircraft_id | Internal aircraft identity; used to join history, rotations and cases. | AC-001 |
| fault_code | TEXT required | fault_catalog.fault_code | Fictional maintenance-event key; not a real cockpit warning code. | DEMO-25-019 |
| station | TEXT required | airports.iata | IATA airport/station code; linked master or applicability label. | MUC |
| reported_at | TEXT required |  | Reported at as canonical UTC timestamp. | 2026-03-23T06:05:00Z |
| symptom_text | TEXT required |  | Recorded symptom narrative; not a confirmed root cause. | Intermittent cabin-zone temperature indication; recorded intermittently on sector 1. |
| resolution_text | TEXT required |  | Historical narrative; does not authorize repeating a physical maintenance action. | Follow-up engineering review recorded; case closed only after separately authorized action. |
| resolution_class | TEXT required |  | Broad historical outcome category for search context. | INDICATION_CORRECTED / MONITORING_REQUIRED / NO_FAULT_FOUND / REPLACEMENT |
| replaced_part_id | TEXT nullable | parts.part_id | Part recorded as consumed historically, or NULL when no replacement was recorded. | DEMO-PART-005 |
| ground_minutes | INTEGER required |  | Historical synthetic elapsed ground interval; not a causal benchmark or predicted saving. | 184 |
| engineer_id | TEXT required | engineers.engineer_id | Stable engineer identifier. | ENG-MUC-01 |
| status | TEXT required |  | Lifecycle/status enum for defects; see application rules. | CLOSED |
| data_class | TEXT required |  | Provenance label: distinguish synthetic records from public reference facts. | SYNTHETIC |

## work_orders

Linked historical work summaries.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| work_order_id | TEXT required | PK  | Stable work order identifier. | WO-0001 |
| defect_id | TEXT required | defects.defect_id | Stable defect identifier. | HIST-0001 |
| task_reference | TEXT required |  | Task reference for linked historical work summaries. | SIM-HIST-TASK-DEMO-A350-21-047 |
| station | TEXT required | airports.iata | IATA airport/station code; linked master or applicability label. | MUC |
| started_at | TEXT required |  | Started at as canonical UTC timestamp. | 2026-04-24T05:05:00Z |
| completed_at | TEXT required |  | Completed at as canonical UTC timestamp. | 2026-04-24T08:09:00Z |
| status | TEXT required |  | Lifecycle/status enum for work_orders; see application rules. | CLOSED |
| summary | TEXT required |  | Summary for linked historical work summaries. | Follow-up engineering review recorded; case closed only after separately authorized action. |
| data_class | TEXT required |  | Provenance label: distinguish synthetic records from public reference facts. | SYNTHETIC |

## open_deferrals

Open-item evidence for external review.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| deferral_id | TEXT required | PK  | Stable deferral identifier. | DEF-001 |
| aircraft_id | TEXT required | aircraft.aircraft_id | Internal aircraft identity; used to join history, rotations and cases. | AC-001 |
| review_reference | TEXT required |  | Simulation review identifier; not a real MEL item. | SIM-MEL-REVIEW-001 |
| description | TEXT required |  | Description for open-item evidence for external review. | Fictional previously recorded cabin item; cross-item assessment remains with authorized personnel. |
| recorded_at | TEXT required |  | Recorded at as canonical UTC timestamp. | 2026-09-13T08:00:00Z |
| expires_at | TEXT required |  | Expires at as canonical UTC timestamp. | 2026-09-16T08:00:00Z |
| status | TEXT required |  | Lifecycle/status enum for open_deferrals; see application rules. | OPEN |
| interaction_review_required | INTEGER required |  | 0/1 flag requiring an authorized human review of interaction with other open items. | 1 |
| data_class | TEXT required |  | Provenance label: distinguish synthetic records from public reference facts. | SYNTHETIC |

## logistics_quotes

Synthetic transport assumptions.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| quote_id | TEXT required | PK  | Stable quote identifier. | Q-AMS-AIR |
| provider_id | TEXT required | providers.provider_id | Stable provider identifier. | PROV-AMS-LOG |
| origin | TEXT required | airports.iata | IATA airport/station code; linked master or applicability label. | AMS |
| destination | TEXT required | airports.iata | IATA airport/station code; linked master or applicability label. | FRA |
| part_id | TEXT required | parts.part_id | Fictional component catalog identifier; not an OEM part number. | DEMO-CZT-100 |
| mode | TEXT required |  | Mode for synthetic transport assumptions. | AIR / ROAD |
| source_prep_minutes | INTEGER required |  | Synthetic packaging/source-tender preparation duration. | 30 |
| available_from_utc | TEXT required |  | Earliest resource/quote availability; for fleet status, station is an inbound target until this time. | 2026-09-14T06:15:00Z |
| cutoff_utc | TEXT nullable |  | Latest tender time for this fictional air movement; NULL for road. | 2026-09-14T07:10:00Z |
| departure_utc | TEXT nullable |  | Departure utc as canonical UTC timestamp. | 2026-09-14T08:10:00Z |
| arrival_utc | TEXT nullable |  | Arrival utc as canonical UTC timestamp. | 2026-09-14T09:20:00Z |
| transit_minutes | INTEGER required |  | Quoted synthetic transport duration; not inferred merely from distance. | 70 |
| destination_handling_minutes | INTEGER required |  | Synthetic arrival clearance/collection/last-mile duration. | 60 |
| cost_eur | REAL required |  | Synthetic cost eur value; not a real price or booking. | 580.0 |
| valid_until_utc | TEXT required |  | Valid until utc as canonical UTC timestamp. | 2026-09-14T07:00:00Z |
| capacity_confirmed | INTEGER required |  | Fixture 0/1 quote capacity confirmation, not a booked shipment. | 1 |
| customs_ready | INTEGER required |  | Fixture 0/1 documentation assumption, not customs clearance. | 1 |
| data_class | TEXT required |  | Provenance label: distinguish synthetic records from public reference facts. | SYNTHETIC |

## fleet_status

Committed/inbound resource availability.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| aircraft_id | TEXT required | PK aircraft.aircraft_id | Internal aircraft identity; used to join history, rotations and cases. | AC-002 |
| station | TEXT required | airports.iata | IATA airport/station code; linked master or applicability label. | FRA |
| available_from_utc | TEXT required |  | Earliest resource/quote availability; for fleet status, station is an inbound target until this time. | 2026-09-14T06:30:00Z |
| allocated_flight_id | TEXT nullable | flights.flight_id | Existing aircraft commitment; presence on the ground is not spare availability. | F-02-0-B |
| status | TEXT required |  | Lifecycle/status enum for fleet_status; see application rules. | ALLOCATED / INBOUND_ALLOCATED |
| compatible_crew | INTEGER required |  | 0/1 preliminary aircraft-swap compatibility flag; not legal crew approval. | 1 |
| last_verified_at | TEXT required |  | Source-snapshot verification time used for freshness checks. | 2026-09-14T06:00:00Z |
| data_class | TEXT required |  | Provenance label: distinguish synthetic records from public reference facts. | SYNTHETIC |

## communications

Context and untrusted message fixtures.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| message_id | TEXT required | PK  | Stable message identifier. | MSG-001 |
| operator_id | TEXT required | operators.operator_id | Tenant/operator ownership key; must not be inferred from model prose. | SIM-AIR |
| sender | TEXT required |  | Sender for context and untrusted message fixtures. | mcc@demo-air.example.invalid |
| recipient | TEXT required |  | Recipient for context and untrusted message fixtures. | fra.mro@example.invalid |
| subject | TEXT required |  | Subject for context and untrusted message fixtures. | Pre-arrival case acknowledgement |
| received_at | TEXT required |  | Received at as canonical UTC timestamp. | 2026-09-14T06:04:00Z |
| body | TEXT required |  | Body for context and untrusted message fixtures. | Received cabin-zone indication report. Ground preparation authorized; no instruction to flight crew. |
| trust_status | TEXT required |  | Ingestion trust label. UNTRUSTED content cannot be retrieved as authority. | TRUSTED / UNTRUSTED |
| related_entity | TEXT required |  | Related entity for context and untrusted message fixtures. | AC-001 |
| data_class | TEXT required |  | Provenance label: distinguish synthetic records from public reference facts. | SYNTHETIC |

## documents

Applicability/trust/effectivity metadata.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| doc_id | TEXT required | PK  | Stable doc identifier. | OTHER-PRIVATE-R1 |
| operator_id | TEXT required | operators.operator_id | Tenant/operator ownership key; must not be inferred from model prose. | OTHER-AIR |
| title | TEXT required |  | Title for applicability/trust/effectivity metadata. | Pre-arrival cabin-zone indication planning brief |
| doc_type | TEXT required |  | Planning, review, SOP or contextual knowledge category. | DISPATCH_REVIEW / ENGINEERING_NOTE / EXTERNAL / HISTORICAL / LOGISTICS / OPERATIONS / PLANNING / RESOURCE / SOP / STATION / STORES |
| aircraft_type | TEXT required |  | Aircraft model applicability label. | A350-900 |
| config_code | TEXT required |  | Operator-specific fictional configuration applicability code. | CAB-C01 |
| station | TEXT required |  | IATA airport/station code; linked master or applicability label. | ALL |
| revision | TEXT required |  | Document revision identifier; lexical ordering is not used to choose a revision. | 3 |
| valid_from | TEXT required |  | Inclusive beginning of applicability/authorization in canonical UTC. | 2026-09-01T00:00:00Z |
| valid_to | TEXT required |  | Exclusive end of applicability/authorization in canonical UTC. | 2027-09-01T00:00:00Z |
| status | TEXT required |  | Lifecycle/status enum for documents; see application rules. | ACTIVE / RETIRED |
| trust_status | TEXT required |  | Ingestion trust label. UNTRUSTED content cannot be retrieved as authority. | TRUSTED / UNTRUSTED |
| markdown_path | TEXT required |  | Package-relative original fictional document path. | knowledge/markdown/SIM-PROC-21-R3.md |
| pdf_path | TEXT required |  | Package-relative PDF presentation of the same section content. | knowledge/pdf/SIM-PROC-21-R3.pdf |
| sha256 | TEXT required |  | Hash of the Markdown source bytes; package manifest separately covers PDF bytes. | 145628b87adee81c163597b423c89d7f969fd336a7ccac207df43ea62b06e044 |
| data_class | TEXT required |  | Provenance label: distinguish synthetic records from public reference facts. | SYNTHETIC_NOT_FOR_MAINTENANCE |

## doc_chunks

Stable original-text sections.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| chunk_id | TEXT required | PK  | Stable retrieval evidence identifier. | OTHER-PRIVATE-R1#S01 |
| doc_id | TEXT required | documents.doc_id | Stable doc identifier. | SIM-PROC-21-R3 |
| ordinal | INTEGER required |  | Section order within the document. | 1 |
| section | TEXT required |  | Section for stable original-text sections. | Purpose |
| content | TEXT required |  | Content for stable original-text sections. | SIMULATION ONLY. Original fictional planning document. Not an OEM manual, approved MEL, maintenance instruction, flight-... |
| page | INTEGER required |  | Page number in the supplied PDF; all fixture documents have one page. | 1 |

## embeddings

Optional derived local vectors.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| chunk_id | TEXT required | PK doc_chunks.chunk_id | Stable retrieval evidence identifier. |  |
| model | TEXT required |  | Model for optional derived local vectors. |  |
| corpus_hash | TEXT required |  | Hash binding optional embeddings to the exact chunk text corpus. |  |
| vector_json | TEXT required |  | Local embedding vector encoded as JSON. No vector is supplied before indexing. |  |

## cases

Runtime preparation cases.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| case_id | TEXT required | PK  | Stable case identifier. |  |
| operator_id | TEXT required | operators.operator_id | Tenant/operator ownership key; must not be inferred from model prose. |  |
| aircraft_id | TEXT required | aircraft.aircraft_id | Internal aircraft identity; used to join history, rotations and cases. |  |
| event_id | TEXT required |  | Stable event identifier. |  |
| event_hash | TEXT required |  | Hash of the canonical validated event payload. |  |
| event_json | TEXT required |  | Validated event as canonical JSON, including externally supplied permission. |  |
| scenario_id | TEXT required |  | Stable scenario identifier. |  |
| clock_utc | TEXT required |  | Controllable scenario clock, distinct from actual wall-clock audit time. |  |
| state | TEXT required |  | State for runtime preparation cases. |  |
| version | INTEGER required |  | Case concurrency version incremented on analysis or external update. |  |
| plan_json | TEXT nullable |  | Full evidence-backed preparation plan, not a maintenance release. |  |
| plan_hash | TEXT nullable |  | Hash binding an approval request to exactly one plan. |  |
| analysis_mode | TEXT nullable |  | reference or ollama; never silently substitute one for the other. |  |
| created_at | TEXT required |  | Created at as canonical UTC timestamp. |  |

## approvals

Human preparation approval events.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| approval_id | TEXT required | PK  | Stable approval identifier. |  |
| case_id | TEXT required | cases.case_id | Stable case identifier. |  |
| case_version | INTEGER required |  | Version approved by the human persona. |  |
| plan_hash | TEXT required |  | Hash binding an approval request to exactly one plan. |  |
| actor | TEXT required |  | Actor for human preparation approval events. |  |
| decision | TEXT required |  | Decision for human preparation approval events. |  |
| created_at | TEXT required |  | Created at as canonical UTC timestamp. |  |
| idempotency_key | TEXT required |  | Stable client request key; duplicate effective approvals do not repeat actions. |  |

## reservations

Reversible demonstration stock holds.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| reservation_id | TEXT required | PK  | Stable reservation identifier. |  |
| case_id | TEXT required | cases.case_id | Stable case identifier. |  |
| lot_id | TEXT required | inventory_lots.lot_id | Stable lot identifier. |  |
| quantity | INTEGER required |  | Quantity for reversible demonstration stock holds. |  |
| status | TEXT required |  | Lifecycle/status enum for reservations; see application rules. |  |
| created_at | TEXT required |  | Created at as canonical UTC timestamp. |  |
| expires_at | TEXT required |  | Expires at as canonical UTC timestamp. |  |

## outbox

Simulated-only write records.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| message_id | TEXT required | PK  | Stable message identifier. |  |
| case_id | TEXT required | cases.case_id | Stable case identifier. |  |
| action | TEXT required |  | Action for simulated-only write records. |  |
| target | TEXT required |  | Target for simulated-only write records. |  |
| payload_json | TEXT required |  | Simulated action payload; no delivery adapter sends it externally. |  |
| status | TEXT required |  | Lifecycle/status enum for outbox; see application rules. |  |
| created_at | TEXT required |  | Created at as canonical UTC timestamp. |  |

## audit

Local hash-linked execution trail.

| Field | Type / null | Key / reference | Meaning | Example / domain |
|---|---|---|---|---|
| audit_id | INTEGER required | PK  | Stable audit identifier. |  |
| recorded_at_utc | TEXT required |  | Actual application wall-clock audit timestamp. |  |
| scenario_time_utc | TEXT required |  | Fixed/replayed business time. |  |
| actor | TEXT required |  | Actor for local hash-linked execution trail. |  |
| case_id | TEXT nullable |  | Stable case identifier. |  |
| action | TEXT required |  | Action for local hash-linked execution trail. |  |
| detail_json | TEXT required |  | Structured audit detail. |  |
| previous_hash | TEXT required |  | Previous local audit entry hash. |  |
| entry_hash | TEXT required |  | Hash of this audit entry and predecessor; not immutable storage. |  |

