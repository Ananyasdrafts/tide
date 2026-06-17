"""Simulated travelers: people with their own pacing, hesitation, and sensitivity.

These are the population Cairn is built and measured against, and later the many "devices"
federated learning trains across. Each traveler has a stable profile; their behaviour on a
route, how long a step takes, when they hesitate, how stress builds, is generated from that
profile and from how well the guidance fits them (step size, modality, pacing). That lets us
test guidance and personalisation without real users.
"""

from __future__ import annotations

from dataclasses import dataclass

MODALITIES = ("text", "icon", "haptic")


def _clip01(x: float) -> float:
    return float(min(1.0, max(0.0, x)))


@dataclass
class TravelerProfile:
    base_pace: float        # seconds to process and act on one clear step (lower = faster)
    hesitancy: float        # 0..1 baseline tendency to stall at a step or junction
    stress_gain: float      # 0..1 how strongly load and hesitation raise stress
    stress_recovery: float  # 0..1 how fast stress eases when things are calm
    modality: str           # preferred step format: text | icon | haptic


@dataclass
class StepOutcome:
    duration: float         # seconds the traveler took on this step
    hesitated: bool
    stress_after: float     # 0..1


def sample_profiles(n: int, rng) -> list[TravelerProfile]:
    """A diverse population: varied pace, hesitancy, sensitivity, and preferred modality."""
    out = []
    for _ in range(n):
        out.append(TravelerProfile(
            base_pace=float(rng.uniform(2.0, 6.0)),
            hesitancy=float(rng.uniform(0.05, 0.6)),
            stress_gain=float(rng.uniform(0.2, 0.9)),
            stress_recovery=float(rng.uniform(0.1, 0.4)),
            modality=MODALITIES[int(rng.integers(0, len(MODALITIES)))],
        ))
    return out


class Traveler:
    """Generates a traveler's behaviour step by step from their profile and the guidance."""

    def __init__(self, profile: TravelerProfile, rng):
        self.p = profile
        self.rng = rng
        self.stress = 0.0

    def take_step(self, sensory: float, step_load: float, modality: str, cadence: float) -> StepOutcome:
        """One guided step.

        sensory: 0..1 sensory load of this segment of the route.
        step_load: 0..1 cognitive load of the instruction as given (dense / long = higher).
        modality: the format the guidance used this step.
        cadence: 0..1 how rushed the pacing is (1 = the next step is pushed immediately).
        """
        p = self.p
        mod_pen = 0.0 if modality == p.modality else 0.15  # wrong format adds load
        hes_p = _clip01(p.hesitancy + 0.4 * sensory + 0.3 * step_load + 0.3 * cadence
                        + 0.3 * self.stress + mod_pen - 0.4)
        hesitated = self.rng.random() < hes_p
        duration = p.base_pace * (1 + 0.8 * step_load + 0.6 * sensory + (1.5 if hesitated else 0.0))
        rise = p.stress_gain * (0.5 * sensory + 0.4 * step_load + 0.3 * cadence
                                + (0.3 if hesitated else 0.0) + mod_pen)
        self.stress = _clip01(self.stress + rise - p.stress_recovery * (1.0 - cadence))
        return StepOutcome(duration=duration, hesitated=hesitated, stress_after=self.stress)

    def ground(self) -> float:
        """Grounding mode: stress eases faster than normal recovery."""
        self.stress = _clip01(self.stress - 2.0 * self.p.stress_recovery)
        return self.stress
