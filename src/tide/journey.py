"""Walk a traveler through a route under a policy, with grounding, and score the journey.

This is the simulation that ties it together: the campus gives a route, the policy tunes
each step, the traveler reacts from their profile, and when stress runs high the journey
pauses for grounding (which costs time but brings stress back down). The result is the set
of numbers Tide is judged on: how long it took, how much hesitation, how high stress
peaked, how often it tipped into overload.
"""

from __future__ import annotations

from dataclasses import dataclass

from .campus import Campus
from .travelers import Traveler

OVERLOAD = 0.8       # stress at or above this is an overload moment
GROUND_AT = 0.7      # at or above this, guidance pauses for grounding
GROUND_TIME = 20.0   # seconds a grounding pause costs


@dataclass
class JourneyResult:
    total_time: float
    hesitations: int
    peak_stress: float
    overload_events: int
    groundings: int
    completed: bool


def run_journey(campus: Campus, start: str, goal: str, traveler: Traveler, policy) -> JourneyResult:
    route = campus.route(start, goal, sensory_weight=policy.route_weight())
    total_time = 0.0
    hes = 0
    peak = 0.0
    over = 0
    ground = 0
    for a, b in zip(route, route[1:]):
        edge = campus.edge_between(a, b)
        s = policy.settings(traveler.stress)
        out = traveler.take_step(edge.sensory, s.step_load, s.modality, s.cadence)
        total_time += out.duration
        if out.hesitated:
            hes += 1
        peak = max(peak, out.stress_after)
        if out.stress_after >= OVERLOAD:
            over += 1
        if out.stress_after >= GROUND_AT:
            traveler.ground()
            ground += 1
            total_time += GROUND_TIME
    return JourneyResult(total_time, hes, peak, over, ground, True)
