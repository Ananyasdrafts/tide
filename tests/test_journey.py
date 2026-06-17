"""The journey simulation and guidance policies."""

import numpy as np

from cairn.campus import sample_campus
from cairn.guidance import PersonalizedPolicy, StaticPolicy
from cairn.journey import run_journey
from cairn.travelers import Traveler, TravelerProfile


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


def test_ablation_flags_isolate_each_adaptation():
    # modality-only: the modality changes, the step/cadence/route do not
    p = PersonalizedPolicy("haptic", 0.8, ease_pace=False, calm_route=False)
    s = p.settings(0.0, 0.9)
    assert s.modality == "haptic" and s.step_load == 0.4 and s.cadence == 0.5
    assert p.route_weight() == 1.0


def test_low_confidence_is_cautious():
    sure = PersonalizedPolicy("icon", 0.2, confidence=0.9)
    unsure = PersonalizedPolicy("icon", 0.2, confidence=0.2)
    assert sure.settings(0.0).modality == "icon"       # trust a confident guess
    assert unsure.settings(0.0).modality == "text"     # fall back to a safe default
    assert unsure.route_weight() > sure.route_weight()  # and assume more sensitive


def test_anticipation_eases_for_a_busy_upcoming_segment():
    p = PersonalizedPolicy("text", 0.0, use_sensitivity=False, calm_route=False, anticipate=True)
    calm = p.settings(0.0, 0.1)
    busy = p.settings(0.0, 0.9)
    assert busy.step_load < calm.step_load
