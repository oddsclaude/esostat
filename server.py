#!/usr/bin/env python3
"""Esolangs statistics web server. Run fetch.py first to generate data.json."""

import json
from collections import Counter
from flask import Flask, request, jsonify, render_template_string

with open("data.json") as f:
    RAW = json.load(f)

DATA = {lang: [c for c in cats if not c.startswith("Hidden")]
        for lang, cats in RAW.items()}

ALL_CATS = sorted({c for cats in DATA.values() for c in cats})

def filter_langs(include=(), exclude=()):
    result = []
    for lang, cats in DATA.items():
        cat_set = set(cats)
        if all(c in cat_set for c in include) and not any(c in cat_set for c in exclude):
            result.append(lang)
    return sorted(result)

app = Flask(__name__)

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Esolangs Stats</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: monospace; background: #0d0d0f; color: #d4d4d8; padding: 1.5rem; }
h1 { color: #00c8a0; margin-bottom: .4rem; font-size: 1.4rem; }
h2 { color: #a78bfa; margin: 1.1rem 0 .4rem; font-size: .95rem; letter-spacing: .05em; text-transform: uppercase; }
p.sub { color: #6b6b7a; margin-bottom: 1rem; font-size: .85rem; }
.row { display: flex; gap: 1rem; flex-wrap: wrap; }
.col { flex: 1; min-width: 280px; }

.picker { position: relative; }
.picker input[type=text] {
  width: 100%; background: #18181f; border: 1px solid #2a2a3a; color: #d4d4d8;
  padding: .4rem .6rem; font-family: monospace; font-size: .9rem; border-radius: 4px;
}
.picker input[type=text]:focus { outline: none; border-color: #00c8a0; }
.dropdown {
  display: none; position: absolute; z-index: 10; width: 100%;
  max-height: 220px; overflow-y: auto;
  background: #18181f; border: 1px solid #2a2a3a; border-top: none;
  border-radius: 0 0 4px 4px;
}
.dropdown.open { display: block; }
.dropdown div {
  padding: .3rem .6rem; cursor: pointer; font-size: .85rem;
}
.dropdown div:hover, .dropdown div.active { background: #00c8a022; color: #00c8a0; }

.chips { display: flex; flex-wrap: wrap; gap: .3rem; min-height: 32px; margin-top: .4rem; }
.chip {
  display: flex; align-items: center; gap: .3rem;
  background: #18181f; border: 1px solid #2a2a3a;
  border-radius: 4px; padding: .2rem .5rem; font-size: .8rem;
}
.chip.inc { border-color: #00c8a0; color: #00c8a0; }
.chip.exc { border-color: #e04040; color: #e04040; }
.chip button {
  background: none; border: none; color: inherit; cursor: pointer;
  font-size: 1rem; line-height: 1; padding: 0;
}

.go { background: #00c8a0; color: #0d0d0f; border: none; padding: .5rem 1.4rem;
      font-family: monospace; font-size: .95rem; cursor: pointer; border-radius: 4px;
      margin-top: 1rem; }
.go:hover { background: #00e0b5; }

.presets { display: flex; flex-wrap: wrap; gap: .4rem; margin-bottom: .5rem; }
.preset {
  background: #18181f; border: 1px solid #2a2a3a; padding: .3rem .7rem;
  border-radius: 4px; cursor: pointer; font-family: monospace; font-size: .82rem;
  color: #a78bfa;
}
.preset:hover { border-color: #a78bfa; }

#out { margin-top: 1.4rem; }
.box { background: #18181f; border: 1px solid #2a2a3a; padding: .8rem 1rem;
       border-radius: 6px; margin-bottom: .8rem; }
.count { font-size: 2.2rem; color: #00c8a0; font-weight: bold; }
.sub2 { color: #6b6b7a; font-size: .82rem; margin-top: .15rem; }
details summary { cursor: pointer; color: #a78bfa; margin-top: .5rem; font-size: .88rem; }
details ul { max-height: 260px; overflow-y: auto; padding: .4rem 0 0 1rem; }
details li { padding: .1rem 0; font-size: .82rem; }
table { border-collapse: collapse; width: 100%; margin-top: .5rem; }
th { text-align: left; color: #6b6b7a; padding: .3rem .6rem;
     border-bottom: 1px solid #2a2a3a; font-size: .82rem; }
td { padding: .22rem .6rem; border-bottom: 1px solid #1a1a24; font-size: .82rem; }
td:last-child { color: #00c8a0; text-align: right; }
</style>
</head>
<body>
<h1>Esolangs Stats Explorer</h1>
<p class="sub">{{ total }} languages &mdash; use the pickers to include/exclude any category</p>

<h2>Presets</h2>
<div class="presets">
{% for name, inc, exc in presets %}
<button class="preset" onclick='applyPreset({{ inc|tojson }}, {{ exc|tojson }})'>{{ name }}</button>
{% endfor %}
</div>

<div class="row">
  <div class="col">
    <h2>Include (must have ALL)</h2>
    <div class="picker">
      <input type="text" id="inc_search" placeholder="Search categories..." autocomplete="off"
             oninput="search(this,'inc')" onfocus="openDrop('inc')" onblur="closeDrop('inc',300)"
             onkeydown="nav(event,'inc')">
      <div class="dropdown" id="inc_drop"></div>
    </div>
    <div class="chips" id="inc_chips"></div>
  </div>
  <div class="col">
    <h2>Exclude (must have NONE)</h2>
    <div class="picker">
      <input type="text" id="exc_search" placeholder="Search categories..." autocomplete="off"
             oninput="search(this,'exc')" onfocus="openDrop('exc')" onblur="closeDrop('exc',300)"
             onkeydown="nav(event,'exc')">
      <div class="dropdown" id="exc_drop"></div>
    </div>
    <div class="chips" id="exc_chips"></div>
  </div>
</div>

<button class="go" onclick="query()">Query</button>

<div id="out"></div>

<script>
const ALL_CATS = {{ all_cats|tojson }};
const selected = { inc: new Set(), exc: new Set() };
let dropIdx = { inc: -1, exc: -1 };

function filtered(q) {
  const lq = q.toLowerCase();
  return ALL_CATS.filter(c => c.toLowerCase().includes(lq));
}

function renderDrop(kind, q) {
  const drop = document.getElementById(kind + '_drop');
  const items = filtered(q).slice(0, 80);
  drop.innerHTML = items.map((c, i) =>
    `<div data-val="${c}" class="${i===dropIdx[kind]?'active':''}"
          onmousedown="add('${kind}','${c.replace(/'/g,"\\'")}')">
       ${c}${selected[kind].has(c) ? ' ✓' : ''}
     </div>`).join('');
}

function search(el, kind) {
  dropIdx[kind] = -1;
  renderDrop(kind, el.value);
  openDrop(kind);
}

function openDrop(kind) {
  const el = document.getElementById(kind + '_search');
  renderDrop(kind, el.value);
  document.getElementById(kind + '_drop').classList.add('open');
}

function closeDrop(kind, delay) {
  setTimeout(() => document.getElementById(kind+'_drop').classList.remove('open'), delay);
}

function nav(e, kind) {
  const drop = document.getElementById(kind + '_drop');
  const items = drop.querySelectorAll('div');
  if (e.key === 'ArrowDown') { dropIdx[kind] = Math.min(dropIdx[kind]+1, items.length-1); }
  else if (e.key === 'ArrowUp') { dropIdx[kind] = Math.max(dropIdx[kind]-1, 0); }
  else if (e.key === 'Enter') {
    if (dropIdx[kind] >= 0 && items[dropIdx[kind]]) {
      add(kind, items[dropIdx[kind]].dataset.val);
    }
    return;
  } else return;
  items.forEach((d,i) => d.classList.toggle('active', i===dropIdx[kind]));
  if (items[dropIdx[kind]]) items[dropIdx[kind]].scrollIntoView({block:'nearest'});
  e.preventDefault();
}

function add(kind, cat) {
  selected[kind].add(cat);
  renderChips(kind);
  document.getElementById(kind+'_search').value = '';
  dropIdx[kind] = -1;
}

function remove(kind, cat) {
  selected[kind].delete(cat);
  renderChips(kind);
}

function renderChips(kind) {
  const el = document.getElementById(kind+'_chips');
  el.innerHTML = [...selected[kind]].map(c =>
    `<span class="chip ${kind}">${c}<button onclick="remove('${kind}','${c.replace(/'/g,"\\'")}')">&times;</button></span>`
  ).join('');
}

function applyPreset(inc, exc) {
  selected.inc = new Set(inc);
  selected.exc = new Set(exc);
  renderChips('inc');
  renderChips('exc');
  query();
}

async function query() {
  const inc = [...selected.inc];
  const exc = [...selected.exc];
  const r = await fetch('/query', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({include: inc, exclude: exc})
  });
  const d = await r.json();
  document.getElementById('out').innerHTML = `
<div class="box">
  <div class="count">${d.count}</div>
  <div class="sub2">languages match</div>
  ${inc.length ? `<div style="margin-top:.3rem">Include: ${inc.map(c=>`<span style="color:#00c8a0">${c}</span>`).join(', ')}</div>` : ''}
  ${exc.length ? `<div style="margin-top:.2rem">Exclude: ${exc.map(c=>`<span style="color:#e04040">${c}</span>`).join(', ')}</div>` : ''}
  <details><summary>Show all ${d.count} languages</summary>
    <ul>${d.langs.map(l=>`<li>${l}</li>`).join('')}</ul>
  </details>
</div>
<div class="box">
  <h2>Category breakdown (matching langs)</h2>
  <table>
    <tr><th>Category</th><th>#</th></tr>
    ${d.cat_counts.map(([c,n])=>`<tr><td>${c}</td><td>${n}</td></tr>`).join('')}
  </table>
</div>`;
}
</script>
</body>
</html>"""

PRESETS = [
    ("All", [], []),
    ("Turing complete", ["Turing complete"], []),
    ("Turing + stack", ["Turing complete", "Stack-based"], []),
    ("Turing + NOT stack", ["Turing complete"], ["Stack-based"]),
    ("No joke / no BF", [], ["Joke languages", "Brainfuck derivatives"]),
    ("Serious + Turing + not stack", ["Turing complete"], ["Joke languages", "Brainfuck derivatives", "Stack-based"]),
    ("Text-based", ["Text-based"], []),
    ("2D languages", ["Two-dimensional languages"], []),
    ("Queue-based", ["Queue-based"], []),
    ("Functional", ["Functional"], []),
]

@app.route("/")
def index():
    return render_template_string(HTML,
        total=len(DATA),
        all_cats=ALL_CATS,
        presets=PRESETS,
    )

@app.route("/query", methods=["POST"])
def query():
    body = request.get_json()
    inc = body.get("include", [])
    exc = body.get("exclude", [])
    langs = filter_langs(include=inc, exclude=exc)
    cat_counts = Counter(c for lang in langs for c in DATA[lang])
    return jsonify(count=len(langs), langs=langs,
                   include=inc, exclude=exc,
                   cat_counts=cat_counts.most_common(40))

@app.route("/categories")
def categories():
    return jsonify(ALL_CATS)

if __name__ == "__main__":
    app.run(port=5757, debug=False)
