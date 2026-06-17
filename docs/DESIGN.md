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
stress        rises with load + hesitation + time pressure; threshold -> grounding mode
personalize   an on-device model of a person's pacing/hesitation
federated     FedAvg across travelers' local models; no raw data shared
eval          static vs personalised vs federated; hesitation, peak stress, overload, done
demo          campus map + animated journey, the current step, stress meter, grounding
```

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

## build order

1. campus model + calm routing (done first)
2. traveler simulation
3. guidance policy (paced steps + abstention)
4. stress + grounding
5. personalisation + federated learning (FedAvg)
6. simulation harness + honest eval + figures
7. browser demo
8. README, CI, MIT, docs
