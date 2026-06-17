# Tide

An adaptive guidance system for navigating overstimulating public spaces. It turns a goal,
like reaching a lecture hall, into short, paced steps instead of a dense map, learns how the
individual moves, routes around the loud and crowded stretches, and steps in with grounding
before the person is overwhelmed.

These spaces do not overwhelm people because the people lack ability; they overwhelm because
the environment demands constant filtering, decision-making, and orientation at once. Tide
reduces that load: one step at a time, timed to the person.

> Live demo (runs in your browser): **https://ananyasdrafts.github.io/tide/** · design in
> [docs/DESIGN.md](docs/DESIGN.md). Simulation-first.

## what it does

Built from scratch, simulation-first. The engine:

- **campus**: the space as a graph; routing minimises distance plus a penalty on sensory
  load, so it can prefer a calmer way.
- **travelers**: simulated people with their own pace, hesitancy, stress sensitivity, and
  preferred step format (text, icon, haptic).
- **guidance**: a route becomes short, paced steps; lighter and slower as stress rises.
- **journey**: walks a traveler through a route, grounding when stress runs high, and scores
  it (time, hesitation, peak stress, overload).
- **personalisation**: a small on-device model reads a short calibration and predicts the
  person's preferred modality and sensitivity, so guidance can fit them.
- **federated learning**: that model is trained across many simulated people with FedAvg,
  weights only, raw behaviour never leaves the device.

## what I found

On a population of simulated travelers (25 held out):

- **Personalising the guidance roughly removes overload.** Against a static one-size policy,
  overload moments per journey fall from 0.32 to 0.00 and peak stress from 0.54 to 0.20,
  matching an oracle that knows each person's true traits.
- **Federated learning costs almost nothing.** Trained with weights only (data stays local),
  it reaches modality accuracy 0.64 and sensitivity error 0.11, against 0.68 and 0.10 for
  centralised training on pooled data.

![personalised vs static](docs/images/personalization.png)

The honest read: most of the gain comes from adapting the pace and route to a person's
sensitivity, which is predicted well; the modality is a secondary, noisier signal. And the
privacy of federated learning is close to free here, which is the point.

## demo

A browser simulator lets you set how sensitive a traveler is and compare static versus
personalised guidance as they walk to the lecture hall: the route (calmer when
personalised), the paced steps one at a time, the stress meter, and grounding when stress
runs high. **Live at https://ananyasdrafts.github.io/tide/**; see [web/README.md](web/README.md)
to run it locally.

## why it is built in a simulator

Like a flight simulator for the problem: reproducible, no real-user data, and the place to
get the adaptive guidance and the federated personalisation right and measure honestly
whether personalisation reduces hesitation and overload. Real wearables and real spaces come
after.

## run it

```bash
pip install -e ".[dev]"
pytest                      # 18 tests
python scripts/run_eval.py  # the personalisation + federated study, writes the figure
```

## design and scaling

This repo is the simulator: it proves the adaptive guidance and the federated personalisation
with no external data. The full design, including what the real product needs and how it
scales, is in [docs/DESIGN.md](docs/DESIGN.md); the short version:

**The real product (parked).** Beyond the simulator it would use real routing (Google or
Apple Maps APIs) and real phone and wearable signals, and would add the safety layer
(grounding, plus an optional alert to a trusted contact if distress persists). The two hard
pieces are indoor positioning and a sensory-load signal per place, which does not exist as a
dataset. And because this is assistive technology, it needs co-design and testing with
autistic, sensory-sensitive, and anxious people, with IRB and consent. None of that is needed
for the simulation, but the design names all of it.

**MVP and scaling.** The smallest real version is one campus, advancing by user confirmation
plus a few checkpoints, which sidesteps precise indoor positioning. It scales space by space
through universities, employers, and accessibility programs, and two privacy-respecting
network effects build the missing data through use: federated personalisation improves
cold-start as more people contribute weights, and consented passive sensing gradually builds
a sensory-load map of each space.

**Grounded in the literature.** The simulation parameters are set to be directionally
consistent with research, not fit to data: cognitive load theory (short single steps lower
load), wayfinding (people favour fewer-decision routes), sensory-processing work (busy
environments exacerbate overload), slow-breathing evidence (grounding lowers arousal), and
federated averaging (McMahan et al., 2017). Citations in [docs/DESIGN.md](docs/DESIGN.md).

Assistive AI should not replace someone's independence; it should protect it, by giving
information in a form their nervous system can actually use.

## license

MIT
