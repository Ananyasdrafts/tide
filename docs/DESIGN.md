# Tide, design notes

An adaptive guidance system for people who find overstimulating public spaces hard to
navigate, autistic and sensory-sensitive people, people with anxiety, anyone for whom a
crowded campus or transit hub turns a simple errand into an exhausting one. Tide breaks a
goal into short, paced steps, learns how the individual moves, and steps in with grounding
before they are overwhelmed rather than after.

## why this

These spaces do not overwhelm people because the people lack ability. They overwhelm
because the environment demands constant filtering, decision-making, and orientation all at
once. A dense map or a long set of directions adds to that load instead of reducing it. So
Tide gives one step at a time, timed to the person, and routes around the loud and crowded
stretches when it can.

It is the same idea as the rest of my work: a system that notices the build-up early, is
honest when it is unsure, and is built to be kind.

## v1 scope (what this build is)

Built simulation-first, like a flight simulator for the problem, so it is reproducible and
needs no real-user data. Decisions locked:

- **Environment: a campus.** Locations and paths as a graph, the lecture-hall errand as the
  running example.
- **Federated learning: built for real.** A small on-device model of each person's pacing
  and hesitation, trained across many simulated travelers with FedAvg, so the
  privacy-preserving claim is demonstrated, not asserted. Raw behaviour never leaves the
  "device"; only model updates are shared.
- **Stress: simulated.** Modeled from sensory load, hesitation, and time pressure (no
  wearable), so the whole thing runs and demos end to end.

## the pieces

```
campus        the space as a graph; routes minimise distance + a penalty on sensory load
travelers     simulated people: pacing, hesitation tendency, stress sensitivity, step style
guidance      a route -> short, context-timed steps, one at a time; pauses when unsure
stress        rises with load + hesitation; eases the pace before it peaks (anticipation);
              a paired signal (heart-rate spike + stalled movement) can trigger grounding
personalize   an on-device model of a person's pacing/hesitation
federated     FedAvg across travelers' local models; no raw data shared
eval          static vs personalised vs federated; hesitation, peak stress, overload, done
demo          campus map + animated journey, the current step, stress meter, grounding
```

## the experience (what the person sees)

The interface is deliberately low-stimulus, because adding to the load is the failure mode.

- one goal in (reach hall_A), and the route comes back as two to five short steps, shown one
  at a time. Finish a step and the next appears, so there is never a wall of directions.
- a step can be short text, a simple icon, or a subtle haptic cue, whichever the person
  prefers; the modality is part of what gets personalised.
- predictable, user-directed controls: pause, repeat, and "I'm stuck". "I'm stuck" is the
  person's own way to stop the flow and get help, rather than the system pushing on.

## anticipating overload, not just reacting

The point is to ease the pace before overload, not alarm after it. From context (crowd
density, noise, the person's past struggle points on similar routes) the system slows the
cadence of steps or simplifies them as pressure builds. If stress still becomes acute, a
paired physiological signal (a sharp heart-rate rise together with stalled movement, past a
threshold the person sets) shifts it into grounding: rhythmic haptic breathing and simplified
prompts. A manual trigger and an optional auto-alert to a pre-chosen trusted contact, with
live location, are there for when distress persists.

## how the thesis shows up

- **Notices early.** Stress is tracked as it builds; grounding triggers before overload, not
  after, the same early-warning shape as MedMaps and Vigil.
- **Honest when unsure.** At an ambiguous junction, or when its read of the person is weak,
  guidance pauses and says so rather than pushing a confident wrong step. Abstention again.
- **Personal and private.** It adapts to the individual, and the federated setup means the
  adaptation happens without their behaviour leaving their device.

## honest framing

The travelers and the stress signal are simulated; that is stated plainly. The point of v1
is to build the adaptive guidance and the federated personalisation correctly and to
measure, honestly, whether personalisation actually reduces hesitation and overload against
a static baseline. If it does not help in some condition, that is a finding, not something
to hide. Real wearables, real spaces, and on-device deployment are the next steps.

## beyond the simulator

The simulator is where the guidance and the federated personalisation get built and measured
honestly. The product around it would use real routing (Google or Apple Maps APIs) and real
phone and smartwatch signals instead of the simulated campus and stress. On reach: it could
start as a simple app with optional personalisation, then scale through universities,
employers, and accessibility programs, and eventually become a low-stimulus layer embedded in
maps and campus systems, so cognitive accessibility lives in the environment rather than
only in the individual.

The line I keep coming back to: assistive AI should not replace someone's independence, it
should protect it, by giving information in a form their nervous system can actually use.

## what building this needs (data and resources)

**v1 (this build): almost no external data.** Simulation-first by design, so there are no
dataset or API gates, it is reproducible and uses no private data.

- campus: a hand-authored graph (the sample campus; a real indoor map could be imported
  later). No data.
- travelers: generated parametrically. The ranges are grounded in the literature on
  processing speed, cognitive load, and stress under sensory load, that is citations, not a
  dataset, so the simulation is defensible rather than arbitrary.
- guidance, stress, grounding: rule and dynamics models. No data.
- personalisation + federated learning: trained on the simulated travelers' own generated
  behaviour, with FedAvg implemented in code. No external data.
- eval + demo: produced from the simulation. No data.
- tools: numpy, matplotlib, pytest; the demo is plain HTML and JavaScript. No GPU, light
  compute.

**Beyond v1 (the real product): where real data and resources come in, honestly.**

- routing: Google / Apple / Mapbox APIs (keys, cost) outdoors. Indoors is the hard part,
  indoor maps plus positioning (BLE beacons, WiFi fingerprinting, or visual positioning),
  an open problem.
- a sensory-load signal per place (crowd, noise, visual busyness): this largely does not
  exist as a dataset. It would need real-time phone sensing (the mic for noise) or
  crowd-sourced data. A genuine gap, and a possible contribution.
- wearables and stress: HealthKit / Google Fit / device SDKs for heart rate and motion; the
  stress-detection model can be bootstrapped and validated on public affective-computing
  datasets (WESAD and similar) and then adapted. Overload data from the target population is
  scarce and sensitive.
- the people: this is assistive technology, so it needs co-design and testing with autistic,
  sensory-sensitive, and anxious users, and IRB and consent for any study and for the
  emergency-contact feature. Building it without them would be the wrong move.
- delivery: a mobile app and a small backend for federated aggregation; the on-device model
  keeps behaviour private by design.

The split is deliberate: v1 proves the adaptive guidance and the federated personalisation
with zero data gates, and names exactly what real data and access the product needs next.

## build order

1. campus model + calm routing (done first)
2. traveler simulation
3. guidance policy (paced steps + abstention)
4. stress + grounding
5. personalisation + federated learning (FedAvg)
6. simulation harness + honest eval + figures
7. browser demo
8. README, CI, MIT, docs
