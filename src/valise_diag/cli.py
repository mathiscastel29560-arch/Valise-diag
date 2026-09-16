"""Interactive text menu — works fine over SSH or a local serial console, no GUI needed."""
from __future__ import annotations

from .actuators import ActuatorController, ActuatorError
from .config import AppConfig, VehicleProfile
from .dtc import Obd2Client
from .elm327 import ELM327Config, ELM327Serial
from .parameters import ParameterController, ParameterError
from .safety import SafetyGuard, SafetyPolicy, SafetyViolation, VehicleState
from .simulator import SimulatedELM327
from .uds import UDSClient


def _confirm(message: str) -> bool:
    answer = input(f"{message}\nTaper OUI en majuscules pour confirmer : ")
    return answer.strip() == "OUI"


def build_uds_clients(app_config: AppConfig, profile: VehicleProfile):
    uds_by_ecu = {}
    for ecu in profile.ecus:
        if app_config.simulate:
            adapter = SimulatedELM327()
        else:
            adapter = ELM327Serial(ELM327Config(port=app_config.port, baudrate=app_config.baudrate))
            adapter.connect()
        uds_by_ecu[ecu.name] = UDSClient(adapter, ecu.tx_header, ecu.rx_header)
    return uds_by_ecu


def main(app_config: AppConfig, profile: VehicleProfile) -> None:
    print(f"Valise diagnostic — {profile.make} {profile.model} {profile.year}")
    print("ATTENTION : lisez docs/SECURITE.md avant toute action sur les actionneurs ou les paramètres moteur.\n")

    guard = SafetyGuard(
        SafetyPolicy(max_speed_kmh=app_config.max_speed_kmh, require_confirmation=app_config.require_confirmation),
        confirm=_confirm,
    )
    uds_by_ecu = build_uds_clients(app_config, profile)
    ecus_by_name = {ecu.name: ecu for ecu in profile.ecus}
    actuator_ctrl = ActuatorController(uds_by_ecu, ecus_by_name, guard)
    parameter_ctrl = ParameterController(uds_by_ecu, ecus_by_name, guard)

    obd2 = None if app_config.simulate else Obd2Client(app_config.port, app_config.baudrate)

    try:
        _run_menu(obd2, actuator_ctrl, parameter_ctrl)
    finally:
        if obd2 is not None:
            obd2.close()


def _run_menu(obd2, actuator_ctrl: ActuatorController, parameter_ctrl: ParameterController) -> None:
    while True:
        print(
            "\n1) Lire les codes défauts\n"
            "2) Effacer les codes défauts\n"
            "3) Tester un actionneur\n"
            "4) Lire un paramètre ECU\n"
            "5) Écrire un paramètre ECU\n"
            "6) Quitter"
        )
        choice = input("> ").strip()
        try:
            if choice == "1":
                _handle_read_dtc(obd2)
            elif choice == "2":
                _handle_clear_dtc(obd2)
            elif choice == "3":
                _handle_actuator(actuator_ctrl, obd2)
            elif choice == "4":
                _handle_read_param(parameter_ctrl)
            elif choice == "5":
                _handle_write_param(parameter_ctrl, obd2)
            elif choice == "6":
                return
            else:
                print("Choix invalide.")
        except (SafetyViolation, ActuatorError, ParameterError) as exc:
            print(f"Erreur : {exc}")


def _handle_read_dtc(obd2) -> None:
    if obd2 is None:
        print("Non disponible en mode simulation.")
        return
    dtcs = obd2.read_dtcs()
    if not dtcs:
        print("Aucun code défaut.")
    for dtc in dtcs:
        print(f"{dtc.code}: {dtc.description}")


def _handle_clear_dtc(obd2) -> None:
    if obd2 is None:
        print("Non disponible en mode simulation.")
        return
    if input("Confirmer l'effacement des codes défauts ? (oui/non) ").strip().lower() == "oui":
        obd2.clear_dtcs()
        print("Codes défauts effacés.")


def _handle_actuator(actuator_ctrl: ActuatorController, obd2) -> None:
    name = input("Nom de l'actionneur : ").strip()
    state = obd2.vehicle_state() if obd2 else VehicleState()
    actuator_ctrl.activate(name, state)
    print("Test terminé, contrôle rendu à l'ECU.")


def _handle_read_param(parameter_ctrl: ParameterController) -> None:
    name = input("Nom du paramètre : ").strip()
    print(f"{name} = {parameter_ctrl.read(name)}")


def _handle_write_param(parameter_ctrl: ParameterController, obd2) -> None:
    name = input("Nom du paramètre : ").strip()
    value = float(input("Nouvelle valeur : ").strip())
    state = obd2.vehicle_state() if obd2 else VehicleState()
    parameter_ctrl.write(name, value, state)
    print("Paramètre écrit et vérifié.")
