# Tide

An adaptive guidance system for navigating overstimulating public spaces. It turns a goal,
like reaching a lecture hall, into short, paced steps instead of a dense map, learns how the
individual moves, routes around the loud and crowded stretches, and steps in with grounding
before the person is overwhelmed.

These spaces do not overwhelm people because the people lack ability; they overwhelm because
the environment demands constant filtering, decision-making, and orientation at once. Tide
reduces that load: one step at a time, timed to the person.

> Early build, simulation-first. The design is in [docs/DESIGN.md](docs/DESIGN.md).

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

## where it goes

Built in a simulator first. The product around it would use real routing and phone and watch
signals, add a safety layer (grounding, and an optional alert to a trusted contact if
distress persists), and could scale from a simple app to universities, employers, and
accessibility programs, eventually a low-stimulus layer inside maps and campus systems.

Assistive AI should not replace someone's independence; it should protect it, by giving
information in a form their nervous system can actually use.

## license

MIT
