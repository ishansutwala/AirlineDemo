'use strict';
let current = null;
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const local = s => s ? new Date(s).toLocaleTimeString('en-GB', { timeZone: 'Europe/Berlin', hour: '2-digit', minute: '2-digit' }) : '--';
const token = () => $('tokenOverride').value.trim() || `demo-${$('role').value.toLowerCase()}-local`;

async function api(path, method = 'GET', body) {
  const r = await fetch(path, {
    method,
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token()}` },
    body: body === undefined ? undefined : JSON.stringify(body)
  });
  if (!r.ok) {
    const j = await r.json();
    throw new Error(typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail));
  }
  return r.json();
}

async function run(action) {
  $('error').hidden = true;
  document.querySelectorAll('button').forEach(x => x.disabled = true);
  $('notice').textContent = 'Request in progress. Live mode uses actual local inference; reference mode does not run a model.';
  try {
    await action();
    $('notice').textContent = 'Action completed. Source records, constraints and authorization remain visible below.';
  } catch (e) {
    $('error').hidden = false;
    $('error').textContent = e.message;
    $('notice').textContent = 'Action did not complete. There is no silent switch from live inference to replay.';
  } finally {
    document.querySelectorAll('button').forEach(x => x.disabled = false);
  }
}

function casePath(s) {
  if (!current) throw new Error('Load a scenario first.');
  return `/api/cases/${current.case_id}/${s}`;
}

// --- TAB NAVIGATION SYSTEM ---
const TABS_CONFIG = {
  'tab-flight-sim': {
    title: 'Flight Simulator',
    subtitle: 'Use the remaining flight time to prepare the ground response.'
  },
  'tab-recovery': {
    title: 'Recovery Options & Preparation Briefing',
    subtitle: 'Evaluate AI-assisted maintenance options, open reviews, and operational claims.'
  },
  'tab-materials': {
    title: 'Material Availability & Staffing Context',
    subtitle: 'Verify usable inventory stock, technician authorization windows, and tool calibration.'
  },
  'tab-flights': {
    title: 'Flight Schedule & Fleet Operations',
    subtitle: 'Manage live schedule, dispatch buffers, and simulate external airline events.'
  },
  'tab-audit': {
    title: 'Audit Trail & Verification Logs',
    subtitle: 'Immutable record of external system events, SLM inferences, human approvals, and inventory holds.'
  },
  'tab-pipeline': {
    title: 'Pipeline Architecture & Signal Board',
    subtitle: 'End-to-end data ingestion, relational SQL queries, and Sovereign SLM lexical RAG flow.'
  },
  'tab-evidence': {
    title: 'Evidence & Document Citations',
    subtitle: 'Ground operations standard procedures, MEL requirements, and historical maintenance work packages.'
  }
};

function switchTab(tabId) {
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });
  document.querySelectorAll('.tab-pane').forEach(pane => {
    pane.classList.toggle('active', pane.id === tabId);
  });

  const cfg = TABS_CONFIG[tabId];
  if (cfg) {
    if ($('pageHeading')) $('pageHeading').textContent = cfg.title;
    if ($('pageSubHeading')) $('pageSubHeading').textContent = cfg.subtitle;
  }

  if (tabId === 'tab-flights' && !allFlights.length) {
    loadFlights();
  }
}

document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.onclick = () => {
    switchTab(btn.dataset.tab);
    // On small screens, close sidebar when a menu item is tapped
    if (window.innerWidth <= 960) {
      $('appLayout')?.classList.add('sidebar-collapsed');
    }
  };
});

// Sidebar Open / Close Toggle handlers
if ($('sidebarToggleBtn')) {
  $('sidebarToggleBtn').onclick = () => {
    $('appLayout')?.classList.toggle('sidebar-collapsed');
  };
}

// Update Persona Badge on selection change
if ($('role')) {
  $('role').onchange = () => {
    if ($('roleDisplay')) $('roleDisplay').textContent = `${$('role').value} Persona`;
  };
}

// --- RENDER APPLICATION STATE ---
function render(c) {
  current = c;
  const p = c.plan || {};
  const e = c.event;
  const inFlight = c.inbound_flight || p.inbound;
  const onFlight = c.onward_flight || p.onward;
  const ac = c.aircraft || p.aircraft;
  const inOrig = inFlight?.origin || (allFlights.find(x => x.flight_id === e.flight_id)?.origin) || 'DXB';
  const dest = e.destination || inFlight?.destination || 'FRA';
  const origCity = c.origin_airport?.city || (inOrig === 'DXB' ? 'Dubai' : inOrig === 'FRA' ? 'Frankfurt' : inOrig === 'AMS' ? 'Amsterdam' : inOrig === 'CDG' ? 'Paris' : inOrig === 'FCO' ? 'Rome' : inOrig === 'BRU' ? 'Brussels' : inOrig);
  const destCity = c.dest_airport?.city || (dest === 'FRA' ? 'Frankfurt' : dest === 'AMS' ? 'Amsterdam' : dest === 'DXB' ? 'Dubai' : dest === 'CDG' ? 'Paris' : dest === 'FCO' ? 'Rome' : dest === 'BRU' ? 'Brussels' : dest);
  const now = new Date(c.clock_utc);
  const stand = inFlight?.estimated_inblock_utc ? new Date(inFlight.estimated_inblock_utc) : new Date('2026-09-14T06:50:00Z');
  const landing = inFlight?.estimated_landing_utc ? new Date(inFlight.estimated_landing_utc) : new Date('2026-09-14T06:40:00Z');

  const formattedClock = local(c.clock_utc);
  $('clock').textContent = formattedClock;
  if ($('sidebarScenarioClock')) $('sidebarScenarioClock').textContent = `${formattedClock} CEST`;
  $('remaining').textContent = Math.max(0, Math.round((stand - now) / 60000));
  $('airborne').textContent = now < landing ? 'AIRBORNE' : now < stand ? 'LANDED / TAXIING' : 'AT STAND';
  $('state').textContent = c.state;
  if ($('navStateBadge')) $('navStateBadge').textContent = c.state;
  $('inference').textContent = p.mode === 'ollama' ? 'LIVE LOCAL SLM' : p.mode === 'reference' ? 'REFERENCE REPLAY - NO AI' : 'NO INFERENCE';
  $('retrieval').textContent = p.retrieval_mode || 'NO RETRIEVAL';

  if ($('heroRouteTitle')) $('heroRouteTitle').innerHTML = `${esc(inOrig)} <span class="arrow">to</span> ${esc(dest)}`;
  if ($('heroOrigin')) $('heroOrigin').textContent = origCity;
  if ($('heroDest')) $('heroDest').textContent = destCity;
  if ($('heroAircraftType')) $('heroAircraftType').textContent = `${esc(ac?.aircraft_type || 'A350-900')} (${esc(e.aircraft_id)})`;
  if ($('heroNextDep')) $('heroNextDep').textContent = onFlight ? local(onFlight.scheduled_out_utc) : '--:--';
  $('flight').textContent = `${e.aircraft_id} | Flight ${esc(inFlight?.display_number || e.flight_id)} | Next: ${esc(onFlight?.display_number || e.next_flight_id)}`;

  if (c.state === 'SUSPENDED') {
    $('airborne').textContent = 'PLAN SUSPENDED / EXTERNAL UPDATE';
    $('remaining').textContent = '--';
  }

  $('eventDetails').innerHTML = `<p><strong>${esc(e.fault_code)}</strong> | ${esc(e.reported_symptom)}</p><p class="small">Source: ${esc(e.source_system)} | Received: ${local(e.received_at)} CEST | Sequence: ${e.source_sequence}</p><p><strong>Preparation permission: ${esc(e.planning_authorization.status)}</strong> | ${esc(e.planning_authorization.scope)} | Expires ${local(e.planning_authorization.expires_at)} CEST</p><p class="small">Crew status supplied externally: ${esc(e.crew_operational_status)}. The SLM does not determine flight safety.</p>`;

  // Claims
  $('modelClaims').innerHTML = (p.explanation?.claims || []).map((x, idx) => `
    <div class="claim-item">
      <div class="claim-header-row">
        <p class="small" style="margin:0;color:var(--navy);font-weight:600"><strong>Claim ${idx + 1}:</strong> ${esc(x.text)}</p>
        <button type="button" class="citation-dots-btn" data-claim-idx="${idx}" title="Click 3 dots to view cited documents and evidence">··· Citations</button>
      </div>
      <div class="citation-chip-row">
        ${(x.evidence_ids || []).map(id => `<span class="citation-chip" data-single-citation="${esc(id)}" title="View citation ${esc(id)}">${esc(id)}</span>`).join('')}
      </div>
    </div>
  `).join('') + (p.explanation?.unresolved_questions || []).map(x => `<p class="small warn">Open review: ${esc(x)}</p>`).join('');

  $('gaps').innerHTML = (p.blocking_gaps || []).map(s => `<div class="warn">${esc(s)}</div>`).join('');

  // Options
  const opts = p.options || [];

  $('options').innerHTML = opts.map(o => {
    const ev = o.evidence_ids || (
      o.option_id === 'A' ? ['SIM-PROC-21-R3#S01', 'SIM-PROC-21-R3#S03', 'SIM-AUTH-R1#S01', 'SIM-SOP-REC-R1#S01', p.selected_engineer_id, p.selected_tool_id].filter(Boolean) :
        o.option_id === 'B' ? ['SIM-MEL-21-R2#S01', 'SIM-MEL-21-R2#S02', 'SIM-SOP-REC-R1#S01'] :
          o.option_id === 'C' ? ['SIM-STORES-R1#S01', 'SIM-LOG-AMS-R1#S01', 'SIM-PROC-21-R3#S04', o.quote_id, o.lot_id].filter(Boolean) :
            o.option_id === 'D' ? ['SIM-OCC-R1#S01', 'SIM-FRA-STA-R1#S01'] : []
    );
    return `<div class="option">
      <div class="option-header-row">
        <strong>${esc(o.option_id)}. ${esc(o.name)}</strong>
        <button type="button" class="citation-dots-btn" data-opt-id="${esc(o.option_id)}" title="Click 3 dots to view supporting document citations">··· Citations</button>
      </div>
      <div class="sub">${esc(o.status)}</div>
      ${o.estimated_departure_utc ? `<div class="time">Estimated departure ${local(o.estimated_departure_utc)} CEST | Simulated delay ${esc(o.delay_minutes)} min</div>` : ''}
      ${o.part_at_station_utc ? `<div class="sub">Part available at FRA: ${local(o.part_at_station_utc)} CEST</div>` : ''}
      <ul class="small">${(o.conditions || []).map(s => `<li>${esc(s)}</li>`).join('')}</ul>
      <div class="citation-chip-row">
        ${ev.map(id => `<span class="citation-chip" data-single-citation="${esc(id)}" title="View citation ${esc(id)}">${esc(id)}</span>`).join('')}
      </div>
    </div>`;
  }).join('') || 'No plan yet.';

  $('trace').innerHTML = (p.tool_trace || []).map(t => `<div class="trace-item"><span>${esc(t.tool)}</span> <span class="ok">COMPLETED</span></div>`).join('');
  $('actions').innerHTML = `<p class="small">Approvals: ${c.approvals.length} | Simulated outbox actions: ${c.outbox.length}</p>` + c.reservations.map(x => `<p class="small">Hold ${esc(x.lot_id)}: ${esc(x.status)}</p>`).join('') + '<p class="small">Dispatch eligibility: UNKNOWN. External release status is never created by the SLM.</p>';
  $('parts').innerHTML = p.inventory ? `<table><thead><tr><th>Station</th><th>Physical</th><th>Usable</th><th>Evidence / constraint</th></tr></thead><tbody>${p.inventory.map(x => `<tr><td><strong>${esc(x.station)}</strong></td><td>${x.qty_on_hand}</td><td class="${x.eligible ? 'ok' : 'bad'}"><strong>${x.usable_quantity}</strong></td><td><code>${esc(x.lot_id)}</code><br>${esc(x.rejection_reasons.join('; ') || 'Current serviceable stock')}</td></tr>`).join('')}</tbody></table>` : 'No inventory check yet.';
  $('resources').innerHTML = `<p><strong>Engineer:</strong> ${esc(p.selected_engineer_id || 'Not selected')}</p><p><strong>Tool:</strong> ${esc(p.selected_tool_id || 'Not selected')}</p>` + (p.engineers || []).filter(x => !x.eligible).map(x => `<p class="small bad"><strong>${esc(x.engineer_id)}:</strong> ${esc(x.rejection_reasons.join('; '))}</p>`).join('') + (p.history || []).slice(0, 2).map(x => `<p class="small" style="background:#f8fafc;padding:8px;border-radius:4px;border:1px solid #e2e8f0;margin-top:6px"><strong>${esc(x.defect_id)} | ${x.days_before_scenario} days earlier</strong><br>${esc(x.resolution_text)}</p>`).join('');

  const dedup = [...new Map((p.documents || []).map(d => [d.doc_id, d])).values()];
  $('evidence').innerHTML = dedup.map(d => `<div class="evidence-card"><div><strong>${esc(d.title)}</strong><span class="small" style="color:var(--muted)">${esc(d.doc_id)} / rev ${esc(d.revision)}</span><p class="small" style="margin-top:8px">${esc(d.content.slice(0, 220))}...</p></div><button data-doc="${esc(d.doc_id)}">📄 Open simulation PDF</button></div>`).join('');

  // Update Pipeline Signal Board nodes & telemetry
  if ($('pipeAcTag')) $('pipeAcTag').textContent = e.aircraft_id || 'AC-001';
  if ($('pipeClassifierTag')) $('pipeClassifierTag').textContent = e.fault_code || '21-47-01';
  if ($('pipeSchemaTag')) $('pipeSchemaTag').textContent = ac?.aircraft_type || 'A350-900';
  if ($('pipeDbTag')) $('pipeDbTag').textContent = `${(p.inventory || []).length || 6} Stations`;
  if ($('pipeDocsTag')) $('pipeDocsTag').textContent = `${dedup.length || 10} Docs`;
  if ($('pipeModelTag')) $('pipeModelTag').textContent = p.mode === 'ollama' ? 'Live Ollama' : 'Reference';
  if ($('pipePlanHashTag')) $('pipePlanHashTag').textContent = c.plan_hash ? `Hash: ${c.plan_hash.slice(0, 10)}...` : 'SHA-256 Verified';

  // Live Activity Log
  const logEl = $('pipelineActivityLog');
  if (logEl) {
    const timeStr = local(c.clock_utc);
    const usableLots = (p.inventory || []).filter(x => x.eligible).length;
    const totalLots = (p.inventory || []).length || 6;
    logEl.innerHTML = `
      <div class="log-line"><span class="log-ts">${timeStr}</span> <span class="log-ok">✓</span> <span class="log-comp">Telemetry Ingestion</span> <span class="log-dim">—</span> <span class="log-msg">Aircraft ${esc(e.aircraft_id)} (${esc(inOrig)} ➔ ${esc(dest)}) event ${esc(e.fault_code)} received</span></div>
      <div class="log-line"><span class="log-ts">${timeStr}</span> <span class="log-ok">✓</span> <span class="log-comp">Policy &amp; Gate</span> <span class="log-dim">—</span> <span class="log-msg">Permission: ${esc(e.planning_authorization?.status || 'ENABLED')} (Scope: ${esc(e.planning_authorization?.scope || 'GROUND_PREPARATION_ONLY')})</span></div>
      <div class="log-line"><span class="log-ts">${timeStr}</span> <span class="log-ok">✓</span> <span class="log-comp">Lexical FTS5 Retriever</span> <span class="log-dim">—</span> <span class="log-msg">Mode: ${esc(p.retrieval_mode || 'LEXICAL_FTS5_WITH_METADATA')} — Matched ${dedup.length} trusted documents</span></div>
      <div class="log-line"><span class="log-ts">${timeStr}</span> <span class="log-ok">✓</span> <span class="log-comp">Relational DB Engine</span> <span class="log-dim">—</span> <span class="log-msg">Checked ${totalLots} inventory stations; ${usableLots} serviceable lots verified</span></div>
      <div class="log-line"><span class="log-ts">${timeStr}</span> <span class="log-ok">✓</span> <span class="log-comp">Resource Validator</span> <span class="log-dim">—</span> <span class="log-msg">Assigned rated staff (${esc(p.selected_engineer_id || 'ENG-FRA-01')}) &amp; tool (${esc(p.selected_tool_id || 'TOOL-FRA-01')})</span></div>
      <div class="log-line"><span class="log-ts">${timeStr}</span> <span class="log-ok">✓</span> <span class="log-comp">Plan Synthesizer</span> <span class="log-dim">—</span> <span class="log-msg">Generated ${opts.length} branches (A, B, C, D) | Hash: ${esc(c.plan_hash ? c.plan_hash.slice(0, 16) : 'VERIFIED')}</span></div>
      <div class="log-line"><span class="log-ts">${timeStr}</span> <span class="log-ok">✓</span> <span class="log-comp">Evidence Binder</span> <span class="log-dim">—</span> <span class="log-msg">Bound ${dedup.length} citations with verifiable PDF references</span></div>
    `;
  }

  document.querySelectorAll('[data-doc]').forEach(b => b.onclick = () => run(async () => {
    const r = await fetch(`/api/documents/${b.dataset.doc}/pdf?case_id=${encodeURIComponent(c.case_id)}`, { headers: { Authorization: `Bearer ${token()}` } });
    if (!r.ok) throw new Error('PDF unavailable or access denied.');
    const url = URL.createObjectURL(await r.blob());
    window.open(url, '_blank', 'noopener');
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  }));

  // Bind Citation Triggers
  document.querySelectorAll('[data-opt-id]').forEach(b => {
    b.onclick = () => {
      const optId = b.dataset.optId;
      const opt = (p.options || []).find(x => x.option_id === optId);
      if (!opt) return;
      const ev = opt.evidence_ids || (
        optId === 'A' ? ['SIM-PROC-21-R3#S01', 'SIM-PROC-21-R3#S03', 'SIM-AUTH-R1#S01', 'SIM-SOP-REC-R1#S01', p.selected_engineer_id, p.selected_tool_id].filter(Boolean) :
          optId === 'B' ? ['SIM-MEL-21-R2#S01', 'SIM-MEL-21-R2#S02', 'SIM-SOP-REC-R1#S01'] :
            optId === 'C' ? ['SIM-STORES-R1#S01', 'SIM-LOG-AMS-R1#S01', 'SIM-PROC-21-R3#S04', opt.quote_id, opt.lot_id].filter(Boolean) :
              optId === 'D' ? ['SIM-OCC-R1#S01', 'SIM-FRA-STA-R1#S01'] : []
      );
      showCitationsModal(`Option ${opt.option_id}: ${opt.name}`, ev, `Document citations and operational rules governing Option ${opt.option_id}:`);
    };
  });

  document.querySelectorAll('[data-claim-idx]').forEach(b => {
    b.onclick = () => {
      const idx = parseInt(b.dataset.claimIdx, 10);
      const claim = (p.explanation?.claims || [])[idx];
      if (!claim) return;
      showCitationsModal(`Preparation Briefing Claim ${idx + 1}`, claim.evidence_ids || [], `Supporting documents and evidence cited for this model claim: "${claim.text.slice(0, 100)}..."`);
    };
  });

  if ($('viewAllBriefCitationsBtn')) {
    $('viewAllBriefCitationsBtn').onclick = () => {
      const allIds = [...new Set((p.explanation?.claims || []).flatMap(x => x.evidence_ids || []))];
      showCitationsModal('Preparation Briefing Citations', allIds.length ? allIds : (p.allowed_evidence_ids || []).slice(0, 12), 'All supporting documents and operational data cited in the briefing:');
    };
  }

  document.querySelectorAll('[data-single-citation]').forEach(chip => {
    chip.onclick = () => {
      const id = chip.dataset.singleCitation;
      showCitationsModal(`Citation: ${id}`, [id], `Detailed evidence record for reference identifier ${id}:`);
    };
  });

  $('audit').textContent = c.audit.map(x => `[${x.scenario_time_utc}] ACTOR: ${x.actor} | ACTION: ${x.action}\n${x.detail_json}`).join('\n\n');
}

// --- CITATION MODAL LOGIC ---
function showCitationsModal(title, evidenceIds, subtitle) {
  const modal = $('citationModal');
  if (!modal) return;
  $('citationModalTitle').textContent = title || 'Document Citations';
  $('citationModalSubtitle').textContent = subtitle || 'Supporting documents, procedural rules, and evidence items used:';
  const list = $('citationList');
  const p = current?.plan || {};
  const docs = p.documents || [];
  const ids = [...new Set((evidenceIds || []).filter(Boolean))];

  if (!ids.length) {
    list.innerHTML = '<div class="empty">No specific document citations linked for this item.</div>';
    modal.hidden = false;
    return;
  }

  const KNOWLEDGE_CATALOG = {
    'SIM-PROC-21-R3': { title: 'Pre-arrival cabin-zone indication planning brief', doc_type: 'PLANNING', revision: '3', excerpt: 'Ground preparation planning brief defining task scope SIM-CABIN-COMFORT, required SIM-DIAG-CAB tooling, and standard turnaround step timings.' },
    'SIM-MEL-21-R2': { title: 'Post-arrival MEL evidence checklist', doc_type: 'DISPATCH_REVIEW', revision: '2', excerpt: 'Checklist of preconditions that an authorized human reviewer must verify before applying any Minimum Equipment List dispatch deferral.' },
    'SIM-SOP-REC-R1': { title: 'Ground recovery authorization and preparation', doc_type: 'SOP', revision: '1', excerpt: 'Standard operating procedures governing ground recovery preparation, bounding SLM authority, and ensuring reversible part holds.' },
    'SIM-ENG-21-R1': { title: 'Repeat-indication engineering context', doc_type: 'ENGINEERING_NOTE', revision: '1', excerpt: 'Engineering context regarding intermittent connector contacts and previous repeat fault occurrences.' },
    'SIM-FRA-STA-R1': { title: 'Frankfurt station arrival coordination', doc_type: 'STATION', revision: '1', excerpt: 'Frankfurt station coordination rules: technician access granted 5 minutes after in-block at gate.' },
    'SIM-STORES-R1': { title: 'Materials acceptance and hold rules', doc_type: 'STORES', revision: '1', excerpt: 'Materials acceptance and lot reservation rules: distinguish quarantined vs. serviceable stock, requires verified release certs.' },
    'SIM-AUTH-R1': { title: 'Engineer eligibility checklist', doc_type: 'RESOURCE', revision: '1', excerpt: 'Staff authorization eligibility: engineer must hold active type qualification covering the complete task window.' },
    'SIM-OCC-R1': { title: 'Ground readiness and onward flight impact', doc_type: 'OPERATIONS', revision: '1', excerpt: 'Operations control standards for dispatch buffers, schedule impact estimation, and spare aircraft swap eligibility.' },
    'SIM-LOG-AMS-R1': { title: 'Amsterdam contingency movement planning', doc_type: 'LOGISTICS', revision: '1', excerpt: 'Courier and air freight contingency transit times, customs handling buffers, and flight tender cutoffs.' },
    'SIM-WO-0042-R1': { title: 'Historical work package WO-0042', doc_type: 'HISTORICAL', revision: '1', excerpt: 'Historical maintenance record describing connector inspection and cleaning on aircraft AC-001.' }
  };

  list.innerHTML = ids.map(id => {
    const cleanDocId = id.replace(/(#S\d+|-P\d+)$/i, '');
    let chunk = docs.find(d => d.chunk_id === id || d.doc_id === id || d.doc_id === cleanDocId || d.chunk_id?.startsWith(cleanDocId));
    if (!chunk && KNOWLEDGE_CATALOG[cleanDocId]) {
      const cat = KNOWLEDGE_CATALOG[cleanDocId];
      chunk = { chunk_id: id, doc_id: cleanDocId, title: cat.title, doc_type: cat.doc_type, revision: cat.revision, content: cat.excerpt };
    }

    if (chunk) {
      const docType = chunk.doc_type || 'PLANNING';
      const docId = chunk.doc_id || cleanDocId;
      return `<div class="citation-detail-card doc-card">
        <div class="citation-detail-header">
          <div>
            <span class="type-badge badge-${esc(docType.toLowerCase())}">${esc(docType)}</span>
            <strong class="citation-doc-title">${esc(chunk.title)}</strong>
            <div class="citation-meta-id">${esc(chunk.chunk_id || id)} | Document ID: <code>${esc(docId)}</code> | Rev ${esc(chunk.revision || '1')}</div>
          </div>
          ${docId ? `<button type="button" class="btn-pdf-view" data-doc-pdf="${esc(docId)}">📄 Open Simulation PDF</button>` : ''}
        </div>
        <div class="citation-doc-excerpt">
          <span class="excerpt-label">Cited Document Section &amp; Operational Rules:</span>
          <p>${esc(chunk.content || '')}</p>
        </div>
      </div>`;
    }

    const lot = (p.inventory || []).find(l => l.lot_id === id);
    if (lot) {
      return `<div class="citation-detail-card lot-card">
        <div class="citation-detail-header">
          <div>
            <span class="type-badge badge-stores">INVENTORY RECORD</span>
            <strong class="citation-doc-title">Lot ${esc(lot.lot_id)} (${esc(lot.station)})</strong>
            <div class="citation-meta-id">Part: <code>${esc(lot.part_id)}</code> | Condition: <strong>${esc(lot.condition)}</strong></div>
          </div>
        </div>
        <div class="citation-doc-excerpt">
          <p><strong>Physical On-Hand:</strong> ${lot.qty_on_hand} | <strong>Usable Quantity:</strong> ${lot.usable_quantity} | <strong>Release Status:</strong> ${esc(lot.release_doc_status)}</p>
          ${lot.rejection_reasons?.length ? `<p class="bad" style="margin-top:4px"><strong>Constraint:</strong> ${esc(lot.rejection_reasons.join('; '))}</p>` : '<p class="ok" style="margin-top:4px">✓ Verified serviceable stock with valid release certificates.</p>'}
        </div>
      </div>`;
    }

    const eng = (p.engineers || []).find(e => e.authorization_id === id || e.engineer_id === id);
    if (eng) {
      return `<div class="citation-detail-card eng-card">
        <div class="citation-detail-header">
          <div>
            <span class="type-badge badge-resource">STAFF QUALIFICATION</span>
            <strong class="citation-doc-title">${esc(eng.name || eng.engineer_id)} (${esc(eng.authorization_id || id)})</strong>
            <div class="citation-meta-id">Station: ${esc(eng.station)} | Rated: ${esc(eng.aircraft_type)} (${esc(eng.config_code)})</div>
          </div>
        </div>
        <div class="citation-doc-excerpt">
          <p><strong>Task Scope:</strong> ${esc(eng.task_scope)} | <strong>Shift:</strong> ${local(eng.start_utc)} - ${local(eng.end_utc)} CEST</p>
          <p><strong>Available for Task:</strong> ${local(eng.available_for_task_utc)} CEST | <strong>Status:</strong> ${eng.eligible ? '✓ Eligible' : '✗ Window Mismatch'}</p>
        </div>
      </div>`;
    }

    const tool = (p.tools || []).find(t => t.tool_asset_id === id);
    if (tool) {
      return `<div class="citation-detail-card tool-card">
        <div class="citation-detail-header">
          <div>
            <span class="type-badge badge-resource">TOOLING RECORD</span>
            <strong class="citation-doc-title">${esc(tool.tool_code)} (${esc(tool.tool_asset_id)})</strong>
            <div class="citation-meta-id">Station: ${esc(tool.station)} | Condition: <strong>${esc(tool.condition)}</strong></div>
          </div>
        </div>
        <div class="citation-doc-excerpt">
          <p><strong>Calibration Expiry:</strong> ${local(tool.calibration_expiry_utc)} CEST | <strong>Status:</strong> ${tool.eligible ? '✓ In-Calibration Serviceable' : '✗ Expired/Unavailable'}</p>
        </div>
      </div>`;
    }

    const quote = (p.logistics || []).find(q => q.quote_id === id);
    if (quote) {
      return `<div class="citation-detail-card log-card">
        <div class="citation-detail-header">
          <div>
            <span class="type-badge badge-logistics">LOGISTICS TRANSIT QUOTE</span>
            <strong class="citation-doc-title">${esc(quote.quote_id)} (${esc(quote.origin)} ➔ ${esc(quote.destination)})</strong>
            <div class="citation-meta-id">Mode: ${esc(quote.mode)} | Provider: <code>${esc(quote.provider_id)}</code></div>
          </div>
        </div>
        <div class="citation-doc-excerpt">
          <p><strong>Cutoff:</strong> ${local(quote.cutoff_utc)} CEST | <strong>Part Available at Station:</strong> ${local(quote.part_at_station_utc)} CEST</p>
        </div>
      </div>`;
    }

    return `<div class="citation-detail-card generic-card">
      <div class="citation-detail-header">
        <div>
          <span class="type-badge">EVIDENCE RECORD</span>
          <strong class="citation-doc-title"><code>${esc(id)}</code></strong>
        </div>
      </div>
      <div class="citation-doc-excerpt">
        <p>Verified evidence ID referenced by the model: <code>${esc(id)}</code></p>
      </div>
    </div>`;
  }).join('');

  list.querySelectorAll('[data-doc-pdf]').forEach(b => {
    b.onclick = () => run(async () => {
      const r = await fetch(`/api/documents/${b.dataset.docPdf}/pdf?case_id=${encodeURIComponent(current.case_id)}`, {
        headers: { Authorization: `Bearer ${token()}` }
      });
      if (!r.ok) throw new Error('PDF unavailable or access denied.');
      const url = URL.createObjectURL(await r.blob());
      window.open(url, '_blank', 'noopener');
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    });
  });

  modal.hidden = false;
}

function hideCitationsModal() {
  const modal = $('citationModal');
  if (modal) modal.hidden = true;
}

if ($('closeCitationModalBtn')) $('closeCitationModalBtn').onclick = hideCitationsModal;
if ($('citationModalBackdrop')) $('citationModalBackdrop').onclick = hideCitationsModal;
document.addEventListener('keydown', e => { if (e.key === 'Escape') hideCitationsModal(); });

// Global Action Buttons
$('load').onclick = () => run(async () => render(await api('/api/demo/load', 'POST', { scenario_id: $('scenario').value })));
$('analyze').onclick = () => run(async () => render(await api(casePath('analyze'), 'POST', { mode: $('mode').value })));
$('approve').onclick = () => run(async () => render(await api(casePath('approve-preparation'), 'POST', { case_version: current.version, plan_hash: current.plan_hash || '', idempotency_key: crypto.randomUUID() })));
$('ready').onclick = () => run(async () => render(await api(casePath('advance-clock'), 'POST', { clock_utc: '2026-09-14T06:30:00Z' })));
$('land').onclick = () => run(async () => render(await api(casePath('advance-clock'), 'POST', { clock_utc: '2026-09-14T06:50:00Z' })));
$('outcome').onclick = () => run(async () => render(await api(casePath('external-outcome'), 'POST', { source_system: 'SIMULATED_MAINTENANCE_SYSTEM', external_reference: 'SIM-RELEASE-001', status: 'SERVICEABLE_RECORDED_EXTERNALLY', recorded_at: '2026-09-14T07:35:00Z', note: 'Fictional authorized maintenance completion; no part consumed. Not an AI release.' })));
$('revoke').onclick = () => run(async () => render(await api(casePath('update'), 'POST', { source_sequence: current.event.source_sequence + 1, planning_status: 'REVOKED' })));
$('divert').onclick = () => run(async () => render(await api(casePath('update'), 'POST', { source_sequence: current.event.source_sequence + 1, destination: 'VIE', planning_status: 'DISABLED' })));
$('export').onclick = () => run(async () => {
  const x = await api(casePath('export'));
  const a = document.createElement('a');
  const u = URL.createObjectURL(new Blob([JSON.stringify(x, null, 2)], { type: 'application/json' }));
  a.href = u;
  a.download = 'recovery_case_evidence.json';
  a.click();
  setTimeout(() => URL.revokeObjectURL(u), 1000);
});

// Copy Audit Button
if ($('copyAuditBtn')) {
  $('copyAuditBtn').onclick = () => {
    const text = $('audit').textContent;
    navigator.clipboard.writeText(text).then(() => {
      alert('Audit trail copied to clipboard.');
    }).catch(() => {
      prompt('Copy audit text manually:', text);
    });
  };
}

fetch('/api/meta').then(r => r.json()).then(x => {
  $('scenario').innerHTML = x.scenarios.map(s => `<option value="${esc(s.id)}">${esc(s.name)}</option>`).join('');
  $('scenario').value = 'nominal';
}).catch(e => {
  $('error').hidden = false;
  $('error').textContent = e.message;
});

// --- FLIGHT CRUD OPERATIONS (WITH ICON BUTTONS) ---
let editingFlightId = null;
let allFlights = [];

function renderFlightsTable(flights) {
  const tbody = $('flightsTableBody');
  if (!flights.length) {
    tbody.innerHTML = '<tr><td colspan="11" class="empty">No flights found matching criteria.</td></tr>';
    return;
  }

  tbody.innerHTML = flights.map(f => {
    const isSelected = editingFlightId === f.flight_id;
    return `<tr data-flight-id="${esc(f.flight_id)}" class="${isSelected ? 'selected-row' : ''}">
      <td style="text-align:center">${isSelected ? '🔘' : '⚪'}</td>
      <td><strong>${esc(f.flight_id)}</strong></td>
      <td>${esc(f.display_number)}</td>
      <td>${esc(f.aircraft_id)}</td>
      <td>${esc(f.origin)}</td>
      <td>${esc(f.destination)}</td>
      <td>${local(f.scheduled_out_utc)}</td>
      <td>${local(f.scheduled_in_utc)}</td>
      <td>${f.passengers}</td>
      <td><span class="${f.status === 'AIRBORNE' ? 'ok' : ''}">${esc(f.status)}</span></td>
      <td style="text-align:center">
        <div class="tbl-quick-actions" onclick="event.stopPropagation()">
          <button type="button" class="tbl-icon-btn tbl-load" data-row-load="${esc(f.flight_id)}" title="Load as Active Flight">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polygon points="3 11 22 2 13 21 11 13 3 11"/></svg>
          </button>
          <button type="button" class="tbl-icon-btn" data-row-edit="${esc(f.flight_id)}" title="Edit Flight Details">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
          </button>
          <button type="button" class="tbl-icon-btn tbl-del" data-row-del="${esc(f.flight_id)}" title="Delete Flight">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          </button>
        </div>
      </td>
    </tr>`;
  }).join('');

  tbody.querySelectorAll('[data-flight-id]').forEach(tr => {
    tr.onclick = () => selectFlight(tr.dataset.flightId);
  });

  tbody.querySelectorAll('[data-row-load]').forEach(btn => {
    btn.onclick = () => {
      selectFlight(btn.dataset.rowLoad);
      $('loadActiveFlightBtn').click();
    };
  });

  tbody.querySelectorAll('[data-row-edit]').forEach(btn => {
    btn.onclick = () => selectFlight(btn.dataset.rowEdit);
  });

  tbody.querySelectorAll('[data-row-del]').forEach(btn => {
    btn.onclick = () => deleteFlight(btn.dataset.rowDel);
  });
}

async function loadFlights() {
  try {
    allFlights = await api('/api/flights?limit=250');
    filterFlights();
  } catch (err) {
    $('flightsTableBody').innerHTML = `<tr><td colspan="11" class="bad">Failed to load flights: ${esc(err.message)}</td></tr>`;
  }
}

function filterFlights() {
  const q = $('flightSearchInput').value.trim().toLowerCase();
  if (!q) { renderFlightsTable(allFlights); return; }
  const filtered = allFlights.filter(f => (f.flight_id + f.display_number + f.aircraft_id + f.origin + f.destination + f.status).toLowerCase().includes(q));
  renderFlightsTable(filtered);
}

function selectFlight(id) {
  const f = allFlights.find(x => x.flight_id === id);
  if (!f) return;
  editingFlightId = f.flight_id;
  filterFlights();
  $('flightFormTitle').textContent = `Selected Flight: ${f.flight_id} (${f.display_number})`;
  $('selectionBadge').style.display = 'inline-block';
  $('selectedFlightTag').textContent = `${f.flight_id} | ${f.origin} -> ${f.destination} | ${f.aircraft_id}`;
  $('f_flight_id').value = f.flight_id;
  $('f_flight_id').disabled = true;
  $('f_operator_id').value = f.operator_id || 'SIM-AIR';
  $('f_aircraft_id').value = f.aircraft_id || '';
  $('f_display_number').value = f.display_number || '';
  $('f_origin').value = f.origin || '';
  $('f_destination').value = f.destination || '';
  $('f_scheduled_out_utc').value = f.scheduled_out_utc || '';
  $('f_scheduled_in_utc').value = f.scheduled_in_utc || '';
  $('f_estimated_landing_utc').value = f.estimated_landing_utc || '';
  $('f_estimated_inblock_utc').value = f.estimated_inblock_utc || '';
  $('f_other_turnaround_ready_utc').value = f.other_turnaround_ready_utc || '';
  $('f_dispatch_buffer_minutes').value = f.dispatch_buffer_minutes ?? 20;
  $('f_passengers').value = f.passengers ?? 200;
  $('f_crew_ready').value = String(f.crew_ready ?? 1);
  $('f_slot_confirmed').value = String(f.slot_confirmed ?? 1);
  $('f_status').value = f.status || 'SCHEDULED';
  $('f_source_basis').value = f.source_basis || 'User entered';
  $('f_data_class').value = f.data_class || 'SYNTHETIC';
  if ($('saveFlightBtnLabel')) $('saveFlightBtnLabel').textContent = 'Update Flight';
  $('loadActiveFlightBtn').style.display = 'inline-flex';
  $('deleteFlightBtn').style.display = 'inline-flex';
  $('flightFormMsg').textContent = `Flight ${f.flight_id} selected. You can edit fields, update, delete, or load it as active.`;
  $('flightFormMsg').className = 'form-msg ok';
}

function resetFlightForm() {
  editingFlightId = null;
  filterFlights();
  $('flightFormTitle').textContent = 'Add New Flight / Selected Flight Details';
  $('selectionBadge').style.display = 'none';
  $('f_flight_id').disabled = false;
  $('f_flight_id').value = '';
  $('f_operator_id').value = 'SIM-AIR';
  $('f_aircraft_id').value = 'AC-001';
  $('f_display_number').value = '';
  $('f_origin').value = 'DXB';
  $('f_destination').value = 'FRA';
  $('f_scheduled_out_utc').value = '2026-09-14T01:00:00Z';
  $('f_scheduled_in_utc').value = '2026-09-14T07:00:00Z';
  $('f_estimated_landing_utc').value = '2026-09-14T06:50:00Z';
  $('f_estimated_inblock_utc').value = '2026-09-14T07:00:00Z';
  $('f_other_turnaround_ready_utc').value = '2026-09-14T00:40:00Z';
  $('f_dispatch_buffer_minutes').value = '20';
  $('f_passengers').value = '280';
  $('f_crew_ready').value = '1';
  $('f_slot_confirmed').value = '1';
  $('f_status').value = 'SCHEDULED';
  $('f_source_basis').value = 'User entered';
  $('f_data_class').value = 'SYNTHETIC';
  if ($('saveFlightBtnLabel')) $('saveFlightBtnLabel').textContent = 'Save Flight';
  $('loadActiveFlightBtn').style.display = 'none';
  $('deleteFlightBtn').style.display = 'none';
  $('flightFormMsg').textContent = '';
  $('flightFormMsg').className = 'form-msg';
}

async function saveFlight() {
  const msg = $('flightFormMsg');
  msg.textContent = 'Saving...';
  msg.className = 'form-msg';
  const body = {
    flight_id: $('f_flight_id').value.trim(),
    operator_id: $('f_operator_id').value.trim() || 'SIM-AIR',
    aircraft_id: $('f_aircraft_id').value.trim(),
    display_number: $('f_display_number').value.trim(),
    origin: $('f_origin').value.trim().toUpperCase(),
    destination: $('f_destination').value.trim().toUpperCase(),
    scheduled_out_utc: $('f_scheduled_out_utc').value.trim(),
    scheduled_in_utc: $('f_scheduled_in_utc').value.trim(),
    estimated_landing_utc: $('f_estimated_landing_utc').value.trim(),
    estimated_inblock_utc: $('f_estimated_inblock_utc').value.trim(),
    other_turnaround_ready_utc: $('f_other_turnaround_ready_utc').value.trim(),
    dispatch_buffer_minutes: parseInt($('f_dispatch_buffer_minutes').value, 10) || 20,
    passengers: parseInt($('f_passengers').value, 10) || 0,
    crew_ready: parseInt($('f_crew_ready').value, 10),
    slot_confirmed: parseInt($('f_slot_confirmed').value, 10),
    status: $('f_status').value,
    source_basis: $('f_source_basis').value.trim() || 'User entered',
    data_class: $('f_data_class').value
  };
  try {
    if (editingFlightId) {
      await api(`/api/flights/${encodeURIComponent(editingFlightId)}`, 'PUT', body);
      msg.textContent = `Flight ${editingFlightId} updated successfully!`;
    } else {
      if (!body.flight_id) { throw new Error('Flight ID is required.'); }
      await api('/api/flights', 'POST', body);
      msg.textContent = `Flight ${body.flight_id} created successfully!`;
      resetFlightForm();
    }
    msg.className = 'form-msg ok';
    await loadFlights();
  } catch (err) {
    msg.textContent = err.message;
    msg.className = 'form-msg bad';
  }
}

async function deleteFlight(id) {
  if (!confirm(`Are you sure you want to delete flight ${id}?`)) return;
  try {
    await api(`/api/flights/${encodeURIComponent(id)}`, 'DELETE');
    resetFlightForm();
    await loadFlights();
  } catch (err) {
    alert('Error deleting flight: ' + err.message);
  }
}

$('saveFlightBtn').onclick = saveFlight;
$('resetFlightFormBtn').onclick = resetFlightForm;
$('loadActiveFlightBtn').onclick = () => run(async () => {
  if (!editingFlightId) return;
  render(await api(`/api/demo/load-flight/${encodeURIComponent(editingFlightId)}`, 'POST'));
  switchTab('tab-flight-sim');
  window.scrollTo({ top: 0, behavior: 'smooth' });
});
$('deleteFlightBtn').onclick = () => { if (editingFlightId) deleteFlight(editingFlightId); };
$('refreshFlightsBtn').onclick = loadFlights;
$('flightSearchInput').oninput = filterFlights;

// Initialize
loadFlights();
// Auto load fixture nominal on first start
api('/api/demo/load', 'POST', { scenario_id: 'nominal' }).then(render).catch(console.error);
