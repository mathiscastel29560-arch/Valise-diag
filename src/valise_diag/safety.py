"""Guards that every actuator activation or ECU parameter write must pass through."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional


class SafetyViolation(RuntimeError):
    pass


@dataclass
class VehicleState:
    speed_kmh: Optional[float] = None
    rpm: Optional[float] = None
    engine_running: Optional[bool] = None


@dataclass
class SafetyPolicy:
    max_speed_kmh: float = 0.0
    require_confirmation: bool = True


class SafetyGuard:
    """Central checkpoint all actuator/parameter actions go through.

    This does not replace mechanical safety (wheels off the ground, handbrake
    on, bystanders clear of moving parts) — it only stops the software from
    sending a command the operator has not explicitly confirmed while the last
    known vehicle state looks unsafe. Always follow docs/SECURITE.md as well.
    """

    def __init__(self, policy: SafetyPolicy, confirm: Callable[[str], bool]):
        self._policy = policy
        self._confirm = confirm

    def check(
        self,
        action_description: str,
        state: VehicleState,
        requires_stationary: bool = True,
        requires_engine_off: bool = False,
        requires_engine_on: bool = False,
    ) -> None:
        if requires_stationary and state.speed_kmh is not None and state.speed_kmh > self._policy.max_speed_kmh:
            raise SafetyViolation(
                f"Refused: vehicle speed {state.speed_kmh} km/h exceeds the "
                f"{self._policy.max_speed_kmh} km/h limit for '{action_description}'."
            )
        if requires_engine_off and state.engine_running:
            raise SafetyViolation(f"Refused: engine must be off for '{action_description}'.")
        if requires_engine_on and state.engine_running is False:
            raise SafetyViolation(f"Refused: engine must be running for '{action_description}'.")
        if self._policy.require_confirmation and not self._confirm(action_description):
            raise SafetyViolation(f"Cancelled by operator: '{action_description}'.")
