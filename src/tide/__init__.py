"""Tide: adaptive guidance for navigating overstimulating public spaces.

Built simulation-first. The pieces, bottom up:
  campus      - the space as a graph, with calm routing (this module set is first)
  travelers   - simulated people with their own pacing, hesitation, stress sensitivity
  guidance    - a route turned into short, paced steps, pausing when unsure
  stress      - stress that rises with load and hesitation, and a grounding mode
  personalize - an on-device model of a person's pacing, trained with federated learning
"""

__version__ = "0.1.0"
