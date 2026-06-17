# Tide

An adaptive guidance system for navigating overstimulating public spaces. It turns a goal,
like reaching a lecture hall, into short, paced steps instead of a dense map, learns how the
individual moves, routes around the loud and crowded stretches, and steps in with grounding
before the person is overwhelmed.

These spaces do not overwhelm people because the people lack ability; they overwhelm because
the environment demands constant filtering, decision-making, and orientation at once. Tide
reduces that load: one step at a time, timed to the person.

> Early build, simulation-first. The design is in [docs/DESIGN.md](docs/DESIGN.md).

## status

Built from scratch, bottom up. Done so far:

- **campus**: the space as a graph, with routing that minimises distance plus a penalty on
  sensory load (so it can prefer a calmer way).

Next: simulated travelers, paced step-by-step guidance that pauses when unsure, a stress and
grounding model, and on-device personalisation trained with federated learning.

## why it is built in a simulator

Like a flight simulator for the problem: reproducible, no real-user data, and the place to
get the adaptive guidance and the federated personalisation right and measure honestly
whether personalisation reduces hesitation and overload. Real wearables and real spaces come
after.

## run it

```bash
pip install -e ".[dev]"
pytest
```

## license

MIT
