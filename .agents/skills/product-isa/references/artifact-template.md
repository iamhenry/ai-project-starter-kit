# Product ISA Artifact Template

Canonical output: `_ai/docs/ISA.html`, one self-contained HTML file (inline CSS and script, no network). Agents read and edit it as text; people open it in a browser to see live progress.

The template shows final order. Generated artifacts omit empty conditional sections. During the interview, insert newly populated sections into this order rather than creating placeholders. `[Bracketed]` text is placeholder content; replace it, and never copy example content from another project's ISA.

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Product ISA: [Whole app name]</title>
<!--
  Product ISA (product-isa, lifeos-inspired; not LifeOS-compatible). Product source of truth.
  Every contract, criterion and decision element has id equal to its stable ID (id="FTR-001").
  Edit rules: never renumber IDs; split as ISC-012.1; supersede instead of delete;
  update the "updated" row on every edit; never hand-edit Progress numbers.
-->
<style>
  :root{--fg:#1a1a1a;--bg:#fff;--muted:#6b6b6b;--soft:#f2f2f2;--line:#e2e2e2;--accent:#2563eb;--warn:#b42318}
  @media (prefers-color-scheme:dark){:root{--fg:#ededed;--bg:#111;--muted:#9a9a9a;--soft:#1f1f1f;--line:#2e2e2e;--accent:#60a5fa;--warn:#f87171}}
  body{font:15px/1.55 -apple-system,system-ui,sans-serif;color:var(--fg);background:var(--bg);max-width:900px;margin:0 auto;padding:32px 20px 80px}
  h2{margin-top:40px;padding-top:14px;border-top:1px solid var(--line)}
  table{border-collapse:collapse;width:100%;font-size:14px}
  th,td{border-top:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
  th{color:var(--muted)}
  #frontmatter th{width:200px}
  code{background:var(--soft);padding:1px 5px;border-radius:5px}
  .id{color:var(--accent);font-weight:700}
  .muted{color:var(--muted)}
  article{border:1px solid var(--line);border-radius:12px;padding:4px 16px 12px;margin:12px 0}
  dl.contract{display:grid;grid-template-columns:180px 1fr;gap:4px 12px}
  dl.contract dt{color:var(--muted);font-weight:600}
  dl.contract dd{margin:0}
  ul.isc{list-style:none;padding-left:4px}
  ul.isc input{accent-color:var(--accent);margin-right:6px}
  #progress .bar{height:10px;border-radius:999px;background:var(--soft);overflow:hidden;flex:1}
  #progress .bar>i{display:block;height:100%;width:0;background:var(--accent)}
  #progress .overall{display:flex;align-items:center;gap:14px;margin:6px 0 18px}
  #progress .tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px}
  #progress .tile{background:var(--soft);border-radius:12px;padding:12px 14px}
  #progress .tile b{display:block;font-size:26px}
  #progress .tile span{display:block;font-weight:600}
  #progress .tile small{color:var(--muted)}
  #progress table.areas td{border:0;padding:3px 8px 3px 0}
  #progress .warn{margin-top:14px;padding:10px 14px;border-radius:10px;border:1px solid var(--warn)}
</style>
</head>
<body>

<h1>Product ISA: [Whole app name]</h1>

<table id="frontmatter" aria-label="Frontmatter">
  <tr><th>artifact</th><td>product-isa</td></tr>
  <tr><th>format</th><td>lifeos-inspired</td></tr>
  <tr><th>title</th><td>[Whole app name]</td></tr>
  <tr><th>status</th><td>drafting</td></tr>
  <tr><th>clarification_progress</th><td>0/8</td></tr>
  <tr><th>principal_stated_goal</th><td>"[Exact user statement]"</td></tr>
  <tr><th>created</th><td>YYYY-MM-DD</td></tr>
  <tr><th>updated</th><td>YYYY-MM-DD</td></tr>
  <!-- Add <tr><th>progress</th><td>0/N</td></tr> only after Criteria synthesis. -->
</table>

<section id="problem"><h2>Problem</h2>
<p>[What is broken or missing now and why it matters.]</p></section>

<section id="vision"><h2>Vision</h2>
<p>[One to five sentences describing the intended user experience and end state.]</p></section>

<!-- Add #progress together with #criteria at synthesis. -->
<section id="progress" aria-label="Progress"><h2>Progress</h2>
<p class="muted">Counted live from this file: ticked criteria, the owner verification table and the latest result per criterion in Verification. Never edit these numbers; tick boxes and add Verification lines instead.</p>
<noscript><p>Open in a browser with JavaScript for live progress. The frontmatter <code>progress</code> row is the stored count.</p></noscript>
<div class="overall"><div class="bar"><i id="pg-bar"></i></div><b id="pg-pct">0%</b><span id="pg-frac" class="muted">0 / 0</span></div>
<div class="tiles">
  <div class="tile"><b id="pg-done">0</b><span>Completed</span><small>proved PASS</small></div>
  <div class="tile"><b id="pg-in-progress">0</b><span>In progress</span><small>latest result FAIL</small></div>
  <div class="tile"><b id="pg-left">0</b><span>Not started</span><small>no result yet</small></div>
  <div class="tile"><b id="pg-blocked">0</b><span>Blocked</span><small>probe cannot run</small></div>
  <div class="tile"><b id="pg-owner">0 / 0</b><span>Owner checks</span><small>verified by the owner</small></div>
</div>
<h3>By area</h3>
<table class="areas" id="pg-areas"></table>
<div id="pg-blocked-list"></div>
<div id="pg-warn"></div>
</section>

<section id="out-of-scope"><h2>Out of Scope</h2>
<p>[Explicit anti-vision and current non-goals.]</p></section>

<section id="principles"><h2>Principles</h2>
<p>[Optional product-relevant truths. Do not copy ETHOS wholesale.]</p></section>

<section id="constraints"><h2>Constraints</h2>
<p>[Immovable product, trust, platform, privacy, or user-stated mandates.]</p></section>

<section id="existing-capability-baseline"><h2>Existing Capability Baseline</h2>
<p>[Existing products only: concise observed capabilities, identified evidence, and preservation implications. Omit for greenfield products.]</p></section>

<section id="goal"><h2>Goal</h2>
<p>[One to three hard-to-vary sentences defining observable done.]</p></section>

<section id="criteria"><h2>Criteria</h2>
<!-- One <h3> per product area, then one ul.isc. The checkbox must directly follow <li id>. Done = add `checked`. -->
<h3>[Product area]</h3>
<ul class="isc">
  <li id="ISC-001"><input type="checkbox" disabled aria-label="ISC-001"> <span class="id">ISC-001</span>: [Atomic observable claim]</li>
  <li id="ISC-002"><input type="checkbox" disabled aria-label="ISC-002"> <span class="id">ISC-002</span>: Anti: [Atomic prohibited outcome]</li>
</ul>
</section>

<section id="not-yet-specified"><h2>Not yet specified</h2>
<p>[Conditional drafting fog. Must contain no material current-scope behavior at ready.]</p></section>

<section id="evidence-standard"><h2>Evidence Standard</h2>
<p>[At synthesis: identify how probes establish replayable consumer-boundary ground truth, distinguish live, controlled, structural, and contextual evidence, and require <code>BLOCKED</code> when the available channel cannot prove the claim.]</p></section>

<section id="test-strategy"><h2>Test Strategy</h2>
<table id="test-strategy-table">
  <tr><th>ISC</th><th>Anchors to</th><th>Source contracts</th><th>Probe type</th><th>Check</th><th>Pass threshold</th><th>Tool</th></tr>
  <tr><td><a href="#ISC-001">ISC-001</a></td><td>literal</td><td><a href="#FTR-001">FTR-001</a>, <a href="#FLOW-001">FLOW-001</a></td><td>live runtime: behavioral</td><td>[Consumer-boundary probe]</td><td>[Binary threshold]</td><td>[Observation tool and retained evidence]</td></tr>
</table>
<!-- Conditional: rows only the owner can verify. The agent still builds and wires the behavior. -->
<h3 id="owner-verification">Owner verification</h3>
<table id="owner-verification-table">
  <tr><th>ISC</th><th>What the owner checks</th><th>Pass threshold</th></tr>
  <tr><td><a href="#ISC-002">ISC-002</a></td><td>[Manual check and why no agent channel can prove it]</td><td>[Binary threshold]</td></tr>
</table>
</section>

<section id="features"><h2>Features</h2>
<p>This section is the detailed product contract for this <code>product-isa</code> dialect. It is not LifeOS's implementation work-breakdown table.</p>
<!-- Subsections in order: Feature Catalog (FTR), Screen Contracts (SCR), User Flow Contracts (FLOW),
     Action Contracts (ACT), Data Display Contracts (DATA), Edge-State Contracts (EDGE).
     Each contract is one <article id="ID"> using the fields from formats.md as <dt>/<dd> pairs. -->
<h3 id="feature-catalog">Feature Catalog</h3>
<article id="FTR-001"><h4><span class="id">FTR-001</span>: [Feature]</h4>
<dl class="contract"><dt>[Field from formats.md]</dt><dd>[Value]</dd></dl></article>
</section>

<section id="decisions"><h2>Decisions</h2>
<article id="DEC-001"><h3><span class="id">DEC-001</span>: [Decision]</h3>
<dl class="contract"><dt>[Decision Ledger field from formats.md]</dt><dd>[Value]</dd></dl></article>
</section>

<section id="learning"><h2>Learning</h2>
<p>[Conditional, only after actual refutation changes understanding.]</p></section>

<section id="verification"><h2>Verification</h2>
<!-- Conditional. Append one <li> per result; the latest line per ISC wins. Format in formats.md. -->
<ul></ul>
</section>

<script>
// Progress: computed from this file only. Owner rows count toward the total but not toward agent tiles.
(function () {
  var $ = function (id) { return document.getElementById(id); };
  if (!$('pg-bar')) return;
  var all = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };
  var esc = function (s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;'); };
  var leaves = all('#criteria li[id^="ISC-"] > input[type=checkbox]');
  var isDone = {};
  leaves.forEach(function (c) { isDone[c.parentNode.id] = c.checked; });
  var total = leaves.length;
  var done = leaves.filter(function (c) { return c.checked; }).length;
  var pct = total ? Math.round(done * 100 / total) : 0;
  $('pg-bar').style.width = pct + '%';
  $('pg-pct').textContent = pct + '%';
  $('pg-frac').textContent = done + ' / ' + total;

  var owner = all('#owner-verification-table td:first-child a').map(function (a) { return a.textContent.trim(); })
    .filter(function (id) { return id in isDone; });
  var ownerDone = owner.filter(function (id) { return isDone[id]; }).length;
  $('pg-owner').textContent = ownerDone + ' / ' + owner.length;

  var latest = {};
  all('#verification li').forEach(function (li) {
    var m = li.textContent.trim().match(/^(ISC-[0-9.]+):\s*(PASS|FAIL|BLOCKED)\s*-\s*([^;]*)/);
    if (m) latest[m[1]] = { status: m[2], reason: m[3].trim() };
  });
  var open = Object.keys(isDone).filter(function (id) { return !isDone[id] && owner.indexOf(id) === -1; });
  var failing = open.filter(function (id) { return latest[id] && latest[id].status === 'FAIL'; });
  var blocked = open.filter(function (id) { return latest[id] && latest[id].status === 'BLOCKED'; });
  $('pg-done').textContent = done - ownerDone;
  $('pg-in-progress').textContent = failing.length;
  $('pg-blocked').textContent = blocked.length;
  $('pg-left').textContent = open.length - failing.length - blocked.length;
  if (blocked.length) {
    var h = '<h3>Blocked (' + blocked.length + ')</h3><table>';
    blocked.forEach(function (id) { h += '<tr><td><a href="#' + id + '">' + id + '</a></td><td>' + esc(latest[id].reason) + '</td></tr>'; });
    $('pg-blocked-list').innerHTML = h + '</table>';
  }

  var rows = '';
  all('#criteria h3').forEach(function (h3) {
    var ul = h3.nextElementSibling;
    if (!ul || !ul.matches('ul.isc')) return;
    var boxes = all('li[id^="ISC-"] > input[type=checkbox]', ul);
    var d = boxes.filter(function (c) { return c.checked; }).length;
    var w = boxes.length ? Math.round(d * 100 / boxes.length) : 0;
    rows += '<tr><td>' + esc(h3.textContent) + '</td><td style="width:60%"><div class="bar"><i style="width:' + w + '%"></i></div></td><td>' + d + '/' + boxes.length + '</td></tr>';
  });
  $('pg-areas').innerHTML = rows;

  var stored = null;
  all('#frontmatter tr').forEach(function (tr) { if (tr.cells[0].textContent.trim() === 'progress') stored = tr.cells[1].textContent.trim(); });
  var passes = all('#verification li').filter(function (li) { return /^ISC-[0-9.]+:\s*PASS\b/.test(li.textContent.trim()); }).length;
  var problems = [];
  if (stored !== null && stored !== done + '/' + total) problems.push('Frontmatter progress says ' + stored + ', but ' + done + '/' + total + ' boxes are ticked.');
  if (passes < done) problems.push(done + ' boxes are ticked but only ' + passes + ' PASS lines exist in Verification.');
  if (problems.length) $('pg-warn').innerHTML = '<div class="warn">' + esc(problems.join(' ')) + ' Fix the record before continuing.</div>';
})();
</script>
</body>
</html>
```

### HTML rules

- Each section is `<section id="kebab-case-heading">` with an `<h2>`; every stable ID is an element `id` and is linked as `<a href="#ID">`.
- Criteria: one `<h3>` per product area followed directly by one `<ul class="isc">`; each leaf is `<li id="ISC-…">` whose first child is a disabled checkbox. Done means adding `checked`, nothing else.
- A dropped or superseded criterion keeps its `<li id>` but has no checkbox, so it never counts.
- Owner-verified rows appear in both `#test-strategy-table` and `#owner-verification-table`. The script and the hivecall watchdog read these ids and markers; do not rename them.
- Escape `<`, `>`, `&` and quotes in user text. Keep the file self-contained: no external CSS, fonts, scripts or images.

## Frontmatter Lifecycle

Frontmatter fields are rows of `#frontmatter`: `<tr><th>field</th><td>value</td></tr>`.

| Field | Rule |
| --- | --- |
| `artifact` | Always `product-isa` |
| `format` | Always `lifeos-inspired` |
| `status` | Normal climb is `drafting` -> `ready` -> `building` -> `verified`; accepted revisions return to `drafting` until invalidation and readiness gates complete |
| `clarification_progress` | Completed interview categories out of eight |
| `principal_stated_goal` | Exact user statement; change only on explicit revision recorded in Decisions |
| `created` | Set once |
| `updated` | Update on every artifact edit |
| `progress` | Closed leaf ISCs over total; absent before synthesis, `0/N` at ready, `N/N` at verified |

`ready` means the behavior contract can be implemented. It does not mean the app works. `verified` requires every in-scope leaf ISC to close on evidence.

`Existing Capability Baseline` is conditional on an existing product. `Evidence Standard` appears once Test Strategy synthesis begins so implementation agents inherit the proof boundary without needing this skill loaded.
