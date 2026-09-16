import pytest

from valise_diag.safety import SafetyGuard, SafetyPolicy, SafetyViolation, VehicleState


def test_refuses_when_moving():
    guard = SafetyGuard(SafetyPolicy(max_speed_kmh=0), confirm=lambda msg: True)
    with pytest.raises(SafetyViolation):
        guard.check("test", VehicleState(speed_kmh=5), requires_stationary=True)


def test_refuses_when_engine_running_but_required_off():
    guard = SafetyGuard(SafetyPolicy(), confirm=lambda msg: True)
    with pytest.raises(SafetyViolation):
        guard.check("test", VehicleState(engine_running=True), requires_engine_off=True)


def test_refuses_without_confirmation():
    guard = SafetyGuard(SafetyPolicy(require_confirmation=True), confirm=lambda msg: False)
    with pytest.raises(SafetyViolation):
        guard.check("test", VehicleState())


def test_passes_when_safe_and_confirmed():
    guard = SafetyGuard(SafetyPolicy(require_confirmation=True), confirm=lambda msg: True)
    guard.check("test", VehicleState(speed_kmh=0, engine_running=False))
