/* ── app.js — CFG Analyzer Dashboard ── */

'use strict';

// ═══════════════════════════════════════════════════════
// State
// ═══════════════════════════════════════════════════════
const state = {
  editor:          null,
  selectedDataset: null,
  lastResult:      null,
};

// ═══════════════════════════════════════════════════════
// Boot
// ═══════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  initEditor();
  loadDatasets();
});

function initEditor() {
  const ta = document.getElementById('code-editor');
  state.editor = CodeMirror.fromTextArea(ta, {
    mode:           'text/x-csrc',
    theme:          'dracula',
    lineNumbers:    true,
    indentUnit:     4,
    tabSize:        4,
    indentWithTabs: false,
    matchBrackets:  true,
    autofocus:      true,
    extraKeys:      { 'Ctrl-Enter': analyzeCustom },
  });
}

// ═══════════════════════════════════════════════════════
// Input tab switching
// ═══════════════════════════════════════════════════════
function switchInputTab(tab) {
  const panels = { custom: 'panel-custom', dataset: 'panel-dataset' };
  const btns   = { custom: 'tab-custom-btn', dataset: 'tab-dataset-btn' };

  Object.entries(panels).forEach(([key, id]) => {
    document.getElementById(id).classList.toggle('hidden', key !== tab);
  });
  Object.entries(btns).forEach(([key, id]) => {
    document.getElementById(id).classList.toggle('active', key === tab);
  });

  if (tab === 'custom') state.editor.refresh();
}

// ═══════════════════════════════════════════════════════
// Dataset loading
// ═══════════════════════════════════════════════════════
async function loadDatasets() {
  try {
    const res  = await fetch('/api/datasets');
    const list = await res.json();
    renderDatasetGrid(list);
  } catch (e) {
    document.getElementById('dataset-grid').innerHTML =
      '<div style="color:var(--red);font-size:12px;padding:10px">Failed to load datasets</div>';
  }
}

function renderDatasetGrid(datasets) {
  const grid = document.getElementById('dataset-grid');
  if (!datasets.length) {
    grid.innerHTML = '<div style="color:var(--text-muted);font-size:12px;padding:10px">No datasets found</div>';
    return;
  }

  const icons = {
    codenet: '🧩',
    sv_comp: '🛡️',
  };

  grid.innerHTML = datasets.map(ds => `
    <div class="dataset-card" id="ds-${CSS.escape(ds.path)}"
         onclick="selectDataset('${ds.path}')">
      <span class="ds-icon">${icons[ds.category] || '📄'}</span>
      <div class="ds-info">
        <div class="ds-name">${ds.name}</div>
        <div class="ds-path">${ds.path}</div>
      </div>
      <span class="ds-badge badge-${ds.category}">${ds.category}</span>
    </div>
  `).join('');
}

async function selectDataset(path) {
  // Update selected state visually
  document.querySelectorAll('.dataset-card').forEach(c => c.classList.remove('selected'));
  const card = document.getElementById(`ds-${CSS.escape(path)}`);
  if (card) card.classList.add('selected');

  state.selectedDataset = path;
  document.getElementById('analyze-dataset-btn').disabled = false;

  // Load and preview the code in the editor
  try {
    const res  = await fetch(`/api/datasets/${path}`);
    const data = await res.json();
    state.editor.setValue(data.content || '');
  } catch (_) { /* non-critical */ }
}

// ═══════════════════════════════════════════════════════
// Analysis triggers
// ═══════════════════════════════════════════════════════
async function analyzeCustom() {
  const code = state.editor.getValue().trim();
  if (!code) return showNavStatus('Paste some C code first', 'warn');
  await runAnalysis({ code });
}

async function analyzeDataset() {
  if (!state.selectedDataset) return showNavStatus('Select a dataset file first', 'warn');
  await runAnalysis({ filepath: state.selectedDataset });
}

// ═══════════════════════════════════════════════════════
// Core pipeline call
// ═══════════════════════════════════════════════════════
async function runAnalysis(payload) {
  // Remove any lingering error overlay from a previous failed run
  const oldErr = document.getElementById('error-overlay');
  if (oldErr) oldErr.remove();

  showLoading(true);
  setNavStatus('Analyzing…');

  // Animate loading steps
  const steps = document.querySelectorAll('.lstep');
  let stepIdx = 0;
  const stepInterval = setInterval(() => {
    if (stepIdx > 0) steps[stepIdx - 1].classList.replace('active', 'done');
    if (stepIdx < steps.length) {
      steps[stepIdx].classList.add('active');
      stepIdx++;
    }
  }, 400);

  try {
    const resp = await fetch('/api/analyze', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload),
    });
    const data = await resp.json();

    clearInterval(stepInterval);
    steps.forEach(s => { s.classList.remove('active'); s.classList.add('done'); });

    await sleep(300); // let user see all steps done

    if (!data.success) {
      showLoading(false);
      showError(data.error, data.detail);
      setNavStatus('Error', 'error');
      return;
    }

    state.lastResult = data;
    showLoading(false);          // hide loader first
    renderResults(data);         // then show results
    setNavStatus(`Done — ${data.stats.nodes_before} → ${data.stats.nodes_after} blocks`);

  } catch (err) {
    clearInterval(stepInterval);
    showLoading(false);
    showError(String(err));
    setNavStatus('Network error', 'error');
  }
}

// ═══════════════════════════════════════════════════════
// Render results
// ═══════════════════════════════════════════════════════
function renderResults(data) {
  hideWelcome();
  const { stats, optimizations, live_variable_analysis: lva, taint_warnings } = data;

  // Stats
  animateCount('sv-nodes-b', stats.nodes_before);
  animateCount('sv-nodes-a', stats.nodes_after);
  animateCount('sv-edges-b', stats.edges_before);
  animateCount('sv-edges-a', stats.edges_after);
  animateCount('sv-instrs-elim', stats.instrs_eliminated);
  const tw = taint_warnings.length;
  document.getElementById('sv-taint').textContent = tw;
  document.getElementById('sv-taint').style.color = tw > 0 ? 'var(--red)' : 'var(--green)';

  // CFG images
  setCfgImage('before-img', data.before_image, 'before');
  setCfgImage('after-img', data.after_image, 'after');

  // Live variable table
  renderLVTable(lva);

  // Optimizations
  renderOptimizations(optimizations);

  // Taint
  renderTaint(taint_warnings);

  // Switch to first tab
  switchAnalysisTab(
    document.querySelector('.atab-btn[data-atab="live-var"]'),
    'live-var'
  );

  // Show results panel
  document.getElementById('results').classList.remove('hidden');
}

function setCfgImage(imgId, base64Payload, graphKind) {
  const img = document.getElementById(imgId);
  if (!img) return;

  const wrap = img.closest('.cfg-img-wrap');
  if (wrap) wrap.classList.add('loading');

  img.onload = () => {
    if (wrap) wrap.classList.remove('loading');
  };
  img.onerror = () => {
    if (wrap) wrap.classList.remove('loading');
  };

  img.onclick = () => openLightbox(graphKind);
  img.src = `data:image/png;base64,${base64Payload}`;
}

// ─── Live Variable Table ──────────────────────────────
function renderLVTable(lva) {
  const tbody = document.getElementById('lv-table-body');
  tbody.innerHTML = lva.map(row => `
    <tr>
      <td><span class="block-num">${row.block}</span></td>
      <td>
        <div class="instr-list">
          ${row.instructions.length
            ? row.instructions.map(i => `<div class="instr-line">${escHtml(i)}</div>`).join('')
            : '<span class="empty-set">empty block</span>'}
        </div>
      </td>
      <td><div class="set-pills">${pills(row.use,  'use-pill')}</div></td>
      <td><div class="set-pills">${pills(row.def,  'def-pill')}</div></td>
      <td><div class="set-pills">${pills(row.in,   'in-pill')}</div></td>
      <td><div class="set-pills">${pills(row.out,  'out-pill')}</div></td>
    </tr>
  `).join('');
}

function pills(arr, cls) {
  if (!arr || !arr.length) return '<span class="empty-set">∅</span>';
  return arr.map(v => `<span class="set-pill ${cls}">${escHtml(v)}</span>`).join('');
}

// ─── Optimizations ────────────────────────────────────
function renderOptimizations(opt) {
  renderOptCard('cf',     opt.constant_folding || [],  renderFoldChange);
  renderOptCard('licm',   opt.licm || [],              renderFoldChange);
  renderOptCard('dce',    opt.dead_code || [],         renderDeadChange);
  renderUnreachable(opt.unreachable_removed || []);
}

function renderOptCard(key, items, renderFn) {
  const badge = document.getElementById(`badge-${key}`);
  const container = document.getElementById(`items-${key}`);

  badge.textContent = items.length;
  badge.classList.toggle('has-changes', items.length > 0);

  if (!items.length) {
    container.innerHTML = '<div class="opt-empty">No changes detected</div>';
    return;
  }
  container.innerHTML = items.map(renderFn).join('');
}

function renderFoldChange(ch) {
  if (ch.before && ch.after) return `
    <div class="opt-change">
      <div class="opt-change-before">Block ${ch.block}: ${escHtml(ch.before)}</div>
      <div class="opt-change-arrow">↓ folded to</div>
      <div class="opt-change-after">${escHtml(ch.after)}</div>
    </div>`;
  if (ch.removed) return `<div class="opt-change"><div class="opt-removed">Block ${ch.block}: ${escHtml(ch.removed)}</div></div>`;
  return '';
}

function renderDeadChange(ch) {
  if (ch.removed) return `<div class="opt-change"><div class="opt-removed">Block ${ch.block}: ${escHtml(ch.removed)}</div></div>`;
  return renderFoldChange(ch);
}

function renderUnreachable(blocks) {
  const badge = document.getElementById('badge-unreach');
  const container = document.getElementById('items-unreach');
  badge.textContent = blocks.length;
  badge.classList.toggle('has-changes', blocks.length > 0);
  if (!blocks.length) {
    container.innerHTML = '<div class="opt-empty">No unreachable blocks</div>';
    return;
  }
  container.innerHTML = blocks.map(b =>
    `<div class="opt-unreachable">✂️ ${escHtml(b)} removed</div>`
  ).join('');
}

// ─── Taint ────────────────────────────────────────────
function renderTaint(warnings) {
  const el = document.getElementById('taint-content');
  if (!warnings.length) {
    el.innerHTML = `
      <div class="taint-clean">
        <div class="taint-clean-icon">✅</div>
        <div class="taint-clean-title">No Security Vulnerabilities Found</div>
        <div class="taint-clean-sub">No tainted user input reached a printf sink.</div>
      </div>`;
    return;
  }
  el.innerHTML = `
    <div class="taint-info">
      ⚠️ Taint analysis found <strong>${warnings.length}</strong> potential vulnerability${warnings.length > 1 ? 'ies' : 'y'}.
      User-controlled input (scanf) reaches an output sink (printf).
    </div>
    <div class="taint-warnings" style="margin-top:12px">
      ${warnings.map(w => `
        <div class="taint-warning">
          <span class="taint-warning-icon">🚨</span>
          <div class="taint-warning-text">${escHtml(w)}</div>
        </div>`).join('')}
    </div>`;
}

// ═══════════════════════════════════════════════════════
// Analysis tab switching
// ═══════════════════════════════════════════════════════
function switchAnalysisTab(btn, tabId) {
  document.querySelectorAll('.atab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.atab-content').forEach(c => c.classList.remove('active'));
  if (btn) btn.classList.add('active');
  const panel = document.getElementById(`atab-${tabId}`);
  if (panel) panel.classList.add('active');
}

// ═══════════════════════════════════════════════════════
// Lightbox
// ═══════════════════════════════════════════════════════
function openLightbox(which) {
  const src = which === 'before'
    ? document.getElementById('before-img').src
    : document.getElementById('after-img').src;
  document.getElementById('lightbox-img').src = src;
  document.getElementById('lightbox').classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}
function closeLightbox() {
  document.getElementById('lightbox').classList.add('hidden');
  document.body.style.overflow = '';
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeLightbox(); });

// ═══════════════════════════════════════════════════════
// UI helpers
// ═══════════════════════════════════════════════════════
function showLoading(on) {
  document.getElementById('loading-screen').classList.toggle('hidden', !on);
  if (on) {
    // Hide results while loading
    document.getElementById('results').classList.add('hidden');
    // Reset step indicators
    document.querySelectorAll('.lstep').forEach(s => {
      s.classList.remove('active', 'done');
    });
    hideWelcome();
  }
}

function hideWelcome() {
  document.getElementById('welcome-screen').style.display = 'none';
}

function showError(msg, detail) {
  document.getElementById('loading-screen').classList.add('hidden');
  // Remove any prior error overlay
  const old = document.getElementById('error-overlay');
  if (old) old.remove();

  const overlay = document.createElement('div');
  overlay.id = 'error-overlay';
  overlay.style.cssText = 'padding:40px;text-align:center;animation:fadeIn .3s ease';
  overlay.innerHTML = `
    <div style="font-size:40px;margin-bottom:14px">❌</div>
    <div style="font-size:16px;font-weight:700;color:var(--red);margin-bottom:8px">Analysis Failed</div>
    <div style="font-size:13px;color:var(--text-muted);max-width:600px;margin:0 auto;line-height:1.6">${escHtml(msg)}</div>
    ${detail ? `<pre style="text-align:left;margin-top:16px;padding:16px;background:var(--bg3);
      border-radius:8px;font-size:10px;color:var(--text-muted);overflow:auto;max-height:200px">${escHtml(detail)}</pre>` : ''}
    <button onclick="document.getElementById('error-overlay').remove()" style="margin-top:20px;padding:8px 20px;
      background:var(--bg3);border:1px solid var(--border);border-radius:8px;
      color:var(--text);cursor:pointer;font-size:12px">Dismiss</button>
  `;
  document.querySelector('.main-content').appendChild(overlay);
}

function setNavStatus(text, type) {
  const el = document.getElementById('nav-status');
  el.textContent = text;
  el.style.color = type === 'error' ? 'var(--red)'
                 : type === 'warn'  ? 'var(--amber)'
                 : 'var(--text-muted)';
}
function showNavStatus(msg, type) { setNavStatus(msg, type); }

function animateCount(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  let cur = 0;
  const step = Math.ceil(target / 20);
  const iv = setInterval(() => {
    cur = Math.min(cur + step, target);
    el.textContent = cur;
    if (cur >= target) clearInterval(iv);
  }, 30);
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
