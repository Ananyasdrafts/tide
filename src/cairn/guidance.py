"""Guidance policies: how a route is turned into paced steps, and how the steps are tuned.

A policy decides, per step, the cognitive load of the instruction, the modality, the cadence,
and how calm a route to take. The static policy uses one setting for everyone. The
personalised policy adapts to a person, and supports three things the eval looks at:

- ablations: each adaptation (matching modality, easing the pace, taking a calmer route) can
  be turned on or off, to see how much each one contributes.
- anticipation: easing for the segment that is about to be walked, before stress has risen,
  not just reacting to current stress.
- confidence: when the model is unsure about a person, the policy leans cautious (a safe
  default modality, assume more sensitive) rather than confidently applying a guess. This is
  the "honest when unsure" thesis put into the logic.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Settings:
    step_load: float
    modality: str
    cadence: float


@dataclass
class StaticPolicy:
    step_load: float = 0.4
    modality: str = "text"
    cadence: float = 0.5

    def route_weight(self) -> float:
        return 1.0

    def settings(self, stress: float, upcoming_sensory: float = 0.0) -> Settings:
        return Settings(self.step_load, self.modality, self.cadence)


@dataclass
class PersonalizedPolicy:
    modality: str
    sensitivity: float
    match_modality: bool = True
    ease_pace: bool = True
    calm_route: bool = True
    use_sensitivity: bool = True  # ease proactively from the predicted sensitivity
    anticipate: bool = False      # also ease ahead of a busy upcoming segment
    confidence: float = 1.0       # model's confidence in this person's traits, 0..1

    def _cautious(self) -> bool:
        return self.confidence < 0.5

    def route_weight(self) -> float:
        if not self.calm_route:
            return 1.0
        sens = max(self.sensitivity, 0.6) if self._cautious() else self.sensitivity
        return 1.0 + 3.0 * sens

    def settings(self, stress: float, upcoming_sensory: float = 0.0) -> Settings:
        # when unsure, assume the person may be sensitive rather than guess otherwise
        eff_sens = max(self.sensitivity, 0.6) if self._cautious() else self.sensitivity
        if self.ease_pace or self.anticipate:
            drivers = [stress]
            if self.ease_pace and self.use_sensitivity:
                drivers.append(eff_sens)
            if self.anticipate:
                drivers.append(0.9 * upcoming_sensory)  # ease ahead of a busy segment
            ease = max(drivers)
            step_load = 0.4 * (1.0 - 0.6 * ease)
            cadence = 0.6 * (1.0 - 0.7 * ease)
        else:
            step_load, cadence = 0.4, 0.5
        # a low-confidence prediction falls back to a safe default modality
        modality = self.modality if (self.match_modality and not self._cautious()) else "text"
        return Settings(step_load, modality, cadence)
