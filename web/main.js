// main.js - drives the Cairn simulator demo.

import {
  NODES, EDGES, route, edgeBetween, Traveler, routeWeight, settings, OVERLOAD, GROUND_AT,
} from "./engine.js";

const SVGNS = "http://www.w3.org/2000/svg";
const map = document.getElementById("map");
const el = (id) => document.getElementById(id);

let modality = "text";
let mode = "static";
let running = false;
let stuck = false;
let dot;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const pretty = (n) => n.replace("_", " ").replace("hall", "Hall");
const sensColor = (s) => `rgb(${Math.round(80 + 175 * s)}, ${Math.round(180 - 120 * s)}, 90)`;

function buildMap() {
  for (const [u, v, d, s] of EDGES) {
    const [x1, y1] = NODES[u], [x2, y2] = NODES[v];
    const line = document.createElementNS(SVGNS, "line");
    line.setAttribute("x1", x1); line.setAttribute("y1", y1);
    line.setAttribute("x2", x2); line.setAttribute("y2", y2);
    line.setAttribute("stroke", sensColor(s));
    line.setAttribute("stroke-width", 2 + 7 * s);
    line.setAttribute("stroke-linecap", "round");
    map.appendChild(line);
  }
  for (const n in NODES) {
    const [x, y] = NODES[n];
    const c = document.createElementNS(SVGNS, "circle");
    c.setAttribute("cx", x); c.setAttribute("cy", y); c.setAttribute("r", 9);
    c.setAttribute("fill", "#1e293b"); c.setAttribute("stroke", "#64748b");
    map.appendChild(c);
    const t = document.createElementNS(SVGNS, "text");
    t.setAttribute("x", x); t.setAttribute("y", y - 16);
    t.setAttribute("text-anchor", "middle"); t.setAttribute("class", "node-label");
    t.textContent = pretty(n);
    map.appendChild(t);
  }
  dot = document.createElementNS(SVGNS, "circle");
  dot.setAttribute("r", 11); dot.setAttribute("fill", "#22c55e");
  dot.setAttribute("class", "dot"); dot.style.display = "none";
  map.appendChild(dot);
}

function moveDot(node) {
  const [x, y] = NODES[node];
  dot.setAttribute("cx", x); dot.setAttribute("cy", y);
}

function profile() {
  const s = +el("sens").value / 100;
  return {
    sensitivity: s,
    base_pace: 3 + 2 * s,
    hesitancy: 0.1 + 0.4 * s,
    stress_gain: 0.3 + 0.6 * s,
    stress_recovery: 0.28 - 0.12 * s,
    modality,
  };
}

function showStep(next, set) {
  const name = pretty(next);
  let body;
  if (set.modality === "icon") body = `<div class="big">&rarr;</div><div>${name}</div>`;
  else if (set.modality === "haptic") {
    body = `<div class="buzz">• • •</div><div>${name}</div>`;
    if (navigator.vibrate) navigator.vibrate(60);
  } else body = `<div class="instr">Walk to the ${name}.</div>`;
  el("step").innerHTML = `<div class="step-card ${set.modality}">${body}</div>`;
}

function setStress(v) {
  const pct = Math.round(v * 100);
  el("stress-bar").style.width = `${pct}%`;
  el("stress-bar").style.background = v >= OVERLOAD ? "#ef4444" : v >= GROUND_AT ? "#f97316" : "#3b82f6";
  el("stress-val").textContent = `${pct}%`;
}

async function ground(trav) {
  el("grounding").classList.add("show");
  await sleep(2200);
  trav.ground();
  setStress(trav.stress);
  el("grounding").classList.remove("show");
}

async function startJourney() {
  if (running) return;
  running = true; stuck = false;
  el("start").disabled = true; el("stuck").disabled = false;
  el("summary").textContent = "";
  const p = profile();
  const policy = mode === "static" ? { type: "static" }
    : { type: "personalized", modality: p.modality, sensitivity: p.sensitivity };
  const trav = new Traveler(p);
  const path = route("entrance", "hall_B", routeWeight(policy));
  dot.style.display = ""; moveDot(path[0]);
  setStress(0);
  let peak = 0, overload = 0, grounded = 0;
  await sleep(500);

  for (let i = 0; i < path.length - 1 && running; i++) {
    const edge = edgeBetween(path[i], path[i + 1]);
    const set = settings(policy, trav.stress);
    showStep(path[i + 1], set);
    const out = trav.step(edge.s, set.step_load, set.modality, set.cadence);
    moveDot(path[i + 1]);
    setStress(out.stress);
    peak = Math.max(peak, out.stress);
    if (out.stress >= OVERLOAD) overload++;
    // pacing: calmer cadence = more time between steps
    await sleep(700 + 900 * (1 - set.cadence));
    if (stuck || out.stress >= GROUND_AT) { await ground(trav); grounded++; stuck = false; }
  }

  el("step").innerHTML = `<div class="step-card text"><div class="instr">You've reached Hall B.</div></div>`;
  el("summary").innerHTML =
    `peak stress <b>${Math.round(peak * 100)}%</b> &middot; overload moments <b>${overload}</b> ` +
    `&middot; grounding pauses <b>${grounded}</b>. Try the other guidance mode and compare.`;
  running = false;
  el("start").disabled = false; el("stuck").disabled = true;
}

function wireSegments() {
  el("modality").addEventListener("click", (e) => {
    if (!e.target.dataset.m) return;
    modality = e.target.dataset.m;
    [...el("modality").children].forEach((b) => b.classList.toggle("on", b.dataset.m === modality));
  });
  el("mode").addEventListener("click", (e) => {
    if (!e.target.dataset.mode) return;
    mode = e.target.dataset.mode;
    [...el("mode").children].forEach((b) => b.classList.toggle("on", b.dataset.mode === mode));
  });
  el("sens").addEventListener("input", () => {
    const s = +el("sens").value;
    el("sens-label").textContent = s < 33 ? "barely" : s < 66 ? "moderately" : "very";
  });
}

buildMap();
wireSegments();
el("start").addEventListener("click", startJourney);
el("stuck").addEventListener("click", () => { if (running) stuck = true; });
