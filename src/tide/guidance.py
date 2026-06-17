"""Guidance policies: how a route is turned into paced steps, and how the steps are tuned.

A policy decides, per step, the cognitive load of the instruction (how much it asks at
once), the modality (text, icon, or haptic), and the cadence (how rushed the pacing is). It
also decides how calm a route to take. A static policy uses one setting for everyone; a
personalised policy adapts to a person's preferred modality and sensitivity, and eases off
further as stress rises rather than pushing on, the "I'm stuck" instinct made into a rule.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Settings:
    step_load: float   # 0..1 cognitive load of the instruction as given
    modality: str      # text | icon | haptic
    cadence: float     # 0..1 pacing rush (lower = more time between steps)


@dataclass
class StaticPolicy:
    """One setting for everyone: a plain, medium-paced text instruction."""

    step_load: float = 0.4
    modality: str = "text"
    cadence: float = 0.5

    def route_weight(self) -> float:
        return 1.0

    def settings(self, stress: float) -> Settings:
        return Settings(self.step_load, self.modality, self.cadence)


@dataclass
class PersonalizedPolicy:
    """Adapts to the person: their preferred modality, how sensitive they are, and how
    stressed they are right now. More sensitive or more stressed means lighter steps, a
    slower cadence, and a calmer route."""

    modality: str
    sensitivity: float  # 0..1

    def route_weight(self) -> float:
        # avoid busy paths more for more sensitive people
        return 1.0 + 3.0 * self.sensitivity

    def settings(self, stress: float) -> Settings:
        ease = max(self.sensitivity, stress)
        return Settings(
            step_load=0.4 * (1.0 - 0.6 * ease),
            modality=self.modality,
            cadence=0.6 * (1.0 - 0.7 * ease),
        )
