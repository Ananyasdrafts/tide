"""Simulated travelers."""

import numpy as np

from tide.travelers import MODALITIES, Traveler, TravelerProfile, sample_profiles


def _profile(modality="text"):
    return TravelerProfile(base_pace=3.0, hesitancy=0.1, stress_gain=0.6,
                           stress_recovery=0.2, modality=modality)


def test_sample_profiles_in_range():
    profs = sample_profiles(50, np.random.default_rng(0))
    assert len(profs) == 50
    assert all(2.0 <= p.base_pace <= 6.0 for p in profs)
    assert all(p.modality in MODALITIES for p in profs)


def test_calm_guidance_keeps_stress_lower_than_rushed():
    # same profile, two pipelines: calm (light, matching modality, unrushed) vs rushed
    calm = Traveler(_profile("text"), np.random.default_rng(1))
    rushed = Traveler(_profile("text"), np.random.default_rng(1))
    for _ in range(15):
        calm.take_step(sensory=0.2, step_load=0.1, modality="text", cadence=0.1)
        rushed.take_step(sensory=0.8, step_load=0.7, modality="icon", cadence=0.9)
    assert rushed.stress > calm.stress


def test_matching_modality_helps():
    match = Traveler(_profile("haptic"), np.random.default_rng(2))
    mismatch = Traveler(_profile("haptic"), np.random.default_rng(2))
    for _ in range(15):
        match.take_step(0.5, 0.4, modality="haptic", cadence=0.5)
        mismatch.take_step(0.5, 0.4, modality="text", cadence=0.5)
    assert match.stress <= mismatch.stress


def test_grounding_reduces_stress():
    t = Traveler(_profile(), np.random.default_rng(3))
    for _ in range(10):
        t.take_step(0.9, 0.8, modality="icon", cadence=0.9)
    before = t.stress
    t.ground()
    assert t.stress < before


def test_duration_grows_with_load():
    # a heavier, busier step takes longer than a light, calm one (no hesitation path)
    t = Traveler(TravelerProfile(3.0, 0.0, 0.5, 0.2, "text"), np.random.default_rng(4))
    light = t.take_step(0.0, 0.0, "text", 0.0).duration
    heavy = t.take_step(0.9, 0.9, "text", 0.0).duration
    assert heavy > light
