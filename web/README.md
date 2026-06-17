# Tide demo (in-browser simulator)

Watch the idea run: set how sensitive a traveler is, pick their preferred step format, and
compare a static one-size guidance with a personalised one as they walk to the lecture hall.
You see the route (calmer when personalised), the paced steps one at a time, the stress
meter, and grounding when stress runs high. "I'm stuck" pauses for grounding on demand.

It runs a small JavaScript port of the simulation engine; the personalisation model and the
federated training stay in the Python engine (here you set the traits directly to see the
payoff of fitting guidance to a person).

## run it locally

```bash
cd web
python -m http.server 8000
# open http://localhost:8000
```

(Deploys to GitHub Pages once the repo is public.)
