"""The journey simulation and guidance policies."""

import numpy as np

from tide.campus import sample_campus
from tide.guidance import PersonalizedPolicy, StaticPolicy
from tide.journey import run_journey
from tide.travelers import Traveler, TravelerProfile


def _sensitive(modality="haptic"):
    return TravelerProfile(base_pace=4.0, hesitancy=0.3, stress_gain=0.85,
                           stress_recovery=0.15, modality=modality)


def test_journey_completes():
    c = sample_campus()
    t = Traveler(_sensitive(), np.random.default_rng(0))
    r = run_journey(c, "entrance", "hall_A", t, StaticPolicy())
    assert r.completed and r.total_time > 0


def test_personalized_helps_a_sensitive_traveler():
    c = sample_campus()
    prof = _sensitive("haptic")
    static = run_journey(c, "entrance", "hall_A",
                         Traveler(prof, np.random.default_rng(1)), StaticPolicy())
    pers = run_journey(c, "entrance", "hall_A",
                       Traveler(prof, np.random.default_rng(1)),
                       PersonalizedPolicy(modality="haptic", sensitivity=0.85))
    assert pers.peak_stress <= static.peak_stress
    assert pers.overload_events <= static.overload_events


def test_calm_policy_takes_the_quieter_route():
    c = sample_campus()
    # a strongly sensitive personalised policy routes via the courtyard, not the cafeteria
    pol = PersonalizedPolicy(modality="text", sensitivity=0.9)
    route = c.route("entrance", "hall_A", sensory_weight=pol.route_weight())
    assert "courtyard" in route and "cafeteria" not in route
