// engine.js - a small JS port of the Cairn simulation, for the demo.
// Mirrors campus routing, the traveler step model, guidance, and the journey thresholds.

export const MODALITIES = ["text", "icon", "haptic"];

// node positions are for drawing the map
export const NODES = {
  entrance: [70, 250], lobby: [200, 250], cafeteria: [340, 140],
  courtyard: [340, 360], hall_A: [490, 250], hall_B: [620, 250],
};
export const EDGES = [
  ["entrance", "lobby", 10, 0.3],
  ["lobby", "cafeteria", 15, 0.9],   // loud, crowded
  ["cafeteria", "hall_A", 10, 0.5],
  ["lobby", "courtyard", 18, 0.1],   // quiet, longer
  ["courtyard", "hall_A", 14, 0.2],
  ["hall_A", "hall_B", 8, 0.3],
];

export const OVERLOAD = 0.8;
export const GROUND_AT = 0.7;

const clip = (x) => Math.min(1, Math.max(0, x));

function adjacency() {
  const a = {};
  for (const [u, v, d, s] of EDGES) {
    (a[u] ||= []).push([v, d, s]);
    (a[v] ||= []).push([u, d, s]);
  }
  return a;
}

export function route(start, goal, sw) {
  const A = adjacency();
  const dist = { [start]: 0 };
  const prev = {};
  const pq = [[0, start]];
  while (pq.length) {
    pq.sort((a, b) => a[0] - b[0]);
    const [d, u] = pq.shift();
    if (u === goal) break;
    if (d > (dist[u] ?? Infinity)) continue;
    for (const [v, ed, s] of A[u] || []) {
      const nd = d + ed * (1 + sw * s);
      if (nd < (dist[v] ?? Infinity)) { dist[v] = nd; prev[v] = u; pq.push([nd, v]); }
    }
  }
  const path = [goal];
  while (path[path.length - 1] !== start) path.push(prev[path[path.length - 1]]);
  return path.reverse();
}

export function edgeBetween(a, b) {
  for (const [u, v, d, s] of EDGES) if ((u === a && v === b) || (u === b && v === a)) return { d, s };
  return null;
}

export class Traveler {
  constructor(profile) { this.p = profile; this.stress = 0; }
  step(sensory, stepLoad, modality, cadence) {
    const p = this.p;
    const modPen = modality === p.modality ? 0 : 0.15;
    const hesP = clip(p.hesitancy + 0.4 * sensory + 0.3 * stepLoad + 0.3 * cadence
      + 0.3 * this.stress + modPen - 0.4);
    const hesitated = Math.random() < hesP;
    const dur = p.base_pace * (1 + 0.8 * stepLoad + 0.6 * sensory + (hesitated ? 1.5 : 0));
    const rise = p.stress_gain * (0.5 * sensory + 0.4 * stepLoad + 0.3 * cadence
      + (hesitated ? 0.3 : 0) + modPen);
    this.stress = clip(this.stress + rise - p.stress_recovery * (1 - cadence));
    return { dur, hesitated, stress: this.stress };
  }
  ground() { this.stress = clip(this.stress - 2 * this.p.stress_recovery); }
}

export function routeWeight(policy) {
  return policy.type === "static" ? 1.0 : 1.0 + 3.0 * policy.sensitivity;
}
export function settings(policy, stress) {
  if (policy.type === "static") return { step_load: 0.4, modality: "text", cadence: 0.5 };
  const ease = Math.max(policy.sensitivity, stress);
  return { step_load: 0.4 * (1 - 0.6 * ease), modality: policy.modality, cadence: 0.6 * (1 - 0.7 * ease) };
}
