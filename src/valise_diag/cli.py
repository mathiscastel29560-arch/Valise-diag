"""Menu texte principal, organisé en onglets — fonctionne par SSH ou console locale."""
from __future__ import annotations

from typing import Dict

from . import games, netinfo
from .actuators import ActuatorController, ActuatorError
from .boot import show_boot_screen
from .coding_doc import afficher_doc_codage
from .config import AppConfig, INTERFACES, VehicleProfile, save_app_config
from .dtc import Obd2Client
from .kwp1281 import KWP1281Client
from .kwp2000 import SID_CLEAR_DIAGNOSTIC_INFORMATION, SID_READ_DTC_BY_STATUS
from .parameters import ParameterController, ParameterError
from .safety import SafetyGuard, SafetyPolicy, SafetyViolation, VehicleState
from .transport import build_diagnostic_clients, build_kw1281_clients


def _confirm(message: str) -> bool:
    answer = input(f"{message}\nTaper OUI en majuscules pour confirmer : ")
    return answer.strip() == "OUI"


def main(app_config: AppConfig, profile: VehicleProfile, app_config_path: str = "config/app.yaml") -> None:
    show_boot_screen()
    print(f"Valise diagnostic — {profile.make} {profile.model} {profile.year}")
    print(f"Interface active : {app_config.interface.upper()}")
    print("ATTENTION : lisez docs/SECURITE.md avant toute action sur les actionneurs ou les paramètres moteur.\n")

    guard = SafetyGuard(
        SafetyPolicy(max_speed_kmh=app_config.max_speed_kmh, require_confirmation=app_config.require_confirmation),
        confirm=_confirm,
    )

    uds_clients: Dict[str, object] = {}
    kw1281_clients: Dict[str, KWP1281Client] = {}
    if not app_config.simulate or app_config.interface == "obd2":
        uds_clients = build_diagnostic_clients(app_config, profile)
    if app_config.interface == "kkl":
        kw1281_clients = build_kw1281_clients(app_config, profile)

    reachable_ecus = {ecu.name: ecu for ecu in profile.ecus if ecu.name in uds_clients}
    kw1281_ecus = {ecu.name: ecu for ecu in profile.ecus if ecu.name in kw1281_clients}

    actuator_ctrl = ActuatorController(uds_clients, reachable_ecus, guard)
    parameter_ctrl = ParameterController(uds_clients, reachable_ecus, guard)

    obd2 = None
    if app_config.interface == "obd2" and not app_config.simulate:
        obd2 = Obd2Client(app_config.port, app_config.baudrate)

    try:
        _run_top_menu(app_config, app_config_path, profile, guard, obd2, actuator_ctrl, parameter_ctrl,
                      uds_clients, kw1281_clients, reachable_ecus, kw1281_ecus)
    finally:
        if obd2 is not None:
            obd2.close()


def _run_top_menu(app_config, app_config_path, profile, guard, obd2, actuator_ctrl, parameter_ctrl,
                   uds_clients, kw1281_clients, reachable_ecus, kw1281_ecus) -> None:
    while True:
        print(
            "\n=== MENU PRINCIPAL ===\n"
            "1) Diagnostic\n"
            "2) Programmation\n"
            "3) Internet\n"
            "4) Paramètres\n"
            "5) Jeux\n"
            "6) Quitter"
        )
        choice = input("> ").strip()
        if choice == "1":
            _menu_diagnostic(app_config, obd2, actuator_ctrl, uds_clients, kw1281_clients, reachable_ecus, kw1281_ecus)
        elif choice == "2":
            _menu_programmation(app_config, parameter_ctrl)
        elif choice == "3":
            _menu_internet()
        elif choice == "4":
            app_config = _menu_parametres(app_config, app_config_path)
        elif choice == "5":
            _menu_jeux()
        elif choice == "6":
            return
        else:
            print("Choix invalide.")


# --------------------------------------------------------------------------
# Onglet Diagnostic
# --------------------------------------------------------------------------

def _menu_diagnostic(app_config, obd2, actuator_ctrl, uds_clients, kw1281_clients, reachable_ecus, kw1281_ecus) -> None:
    while True:
        print(
            "\n--- DIAGNOSTIC ---\n"
            "1) Lire les codes défauts\n"
            "2) Effacer les codes défauts\n"
            "3) Lecture temps réel\n"
            "4) Tester un actionneur\n"
            "5) Identification ECU\n"
            "6) Retour"
        )
        choice = input("> ").strip()
        try:
            if choice == "1":
                _handle_read_dtc(app_config, obd2, uds_clients, kw1281_clients, reachable_ecus, kw1281_ecus)
            elif choice == "2":
                _handle_clear_dtc(app_config, obd2, uds_clients, kw1281_clients, reachable_ecus, kw1281_ecus)
            elif choice == "3":
                _handle_live_data(app_config, obd2)
            elif choice == "4":
                _handle_actuator(app_config, actuator_ctrl, obd2)
            elif choice == "5":
                _handle_identification(app_config, obd2, reachable_ecus, kw1281_ecus)
            elif choice == "6":
                return
            else:
                print("Choix invalide.")
        except (SafetyViolation, ActuatorError) as exc:
            print(f"Erreur : {exc}")


def _handle_read_dtc(app_config, obd2, uds_clients, kw1281_clients, reachable_ecus, kw1281_ecus) -> None:
    if app_config.interface == "obd2":
        if obd2 is None:
            print("Non disponible en mode simulation.")
            return
        dtcs = obd2.read_dtcs()
        if not dtcs:
            print("Aucun code défaut.")
        for dtc in dtcs:
            print(f"{dtc.code}: {dtc.description}")
        return

    for name, client in uds_clients.items():
        if reachable_ecus[name].protocol != "kwp2000_kline":
            continue
        try:
            raw = client.request(SID_READ_DTC_BY_STATUS, bytes([0x00]))
            print(f"[{name}] codes défauts (hex brut, non décodé) : {raw.hex(' ')}")
        except Exception as exc:  # noqa: BLE001 - surfaced to the operator, not swallowed
            print(f"[{name}] erreur : {exc}")
    for name, client in kw1281_clients.items():
        block_title = kw1281_ecus[name].kw1281_blocks.get("read_fault_codes")
        if block_title is None:
            print(f"[{name}] 'read_fault_codes' non défini dans le profil (section blocks:).")
            continue
        try:
            response = client.request(block_title)
            print(f"[{name}] codes défauts (hex brut, non décodé) : {response.data.hex(' ')}")
        except Exception as exc:  # noqa: BLE001
            print(f"[{name}] erreur : {exc}")


def _handle_clear_dtc(app_config, obd2, uds_clients, kw1281_clients, reachable_ecus, kw1281_ecus) -> None:
    if not _confirm("Confirmer l'effacement des codes défauts"):
        return
    if app_config.interface == "obd2":
        if obd2 is None:
            print("Non disponible en mode simulation.")
            return
        obd2.clear_dtcs()
        print("Codes défauts effacés.")
        return

    for name, client in uds_clients.items():
        if reachable_ecus[name].protocol != "kwp2000_kline":
            continue
        try:
            client.request(SID_CLEAR_DIAGNOSTIC_INFORMATION, bytes([0xFF, 0x00]))
            print(f"[{name}] codes défauts effacés.")
        except Exception as exc:  # noqa: BLE001
            print(f"[{name}] erreur : {exc}")
    for name, client in kw1281_clients.items():
        block_title = kw1281_ecus[name].kw1281_blocks.get("clear_fault_codes")
        if block_title is None:
            print(f"[{name}] 'clear_fault_codes' non défini dans le profil (section blocks:).")
            continue
        try:
            client.request(block_title)
            print(f"[{name}] codes défauts effacés.")
        except Exception as exc:  # noqa: BLE001
            print(f"[{name}] erreur : {exc}")


def _handle_live_data(app_config, obd2) -> None:
    if app_config.interface != "obd2":
        print("Lecture temps réel : utilisez Programmation > Lire un paramètre ECU "
              "(les valeurs temps réel KKL sont définies comme des paramètres dans le profil véhicule).")
        return
    if obd2 is None:
        print("Non disponible en mode simulation.")
        return
    for command in ("RPM", "SPEED", "COOLANT_TEMP"):
        value = obd2.live_value(command)
        print(f"{command} = {value}")


def _handle_actuator(app_config, actuator_ctrl: ActuatorController, obd2) -> None:
    name = input("Nom de l'actionneur : ").strip()
    if app_config.interface == "kkl":
        print("⚠️  Vitesse non surveillée sur l'interface KKL : vérifiez vous-même que le véhicule est à l'arrêt.")
    state = obd2.vehicle_state() if obd2 else VehicleState()
    actuator_ctrl.activate(name, state)
    print("Test terminé, contrôle rendu à l'ECU.")


def _handle_identification(app_config, obd2, reachable_ecus, kw1281_ecus) -> None:
    if app_config.interface == "obd2" and obd2 is not None:
        vin = obd2.live_value("VIN")
        if vin:
            print(f"VIN : {vin}")
    for name, ecu in {**reachable_ecus, **kw1281_ecus}.items():
        print(f"{name}: protocole={ecu.protocol}, adresse={ecu.tx_header}")


# --------------------------------------------------------------------------
# Onglet Programmation
# --------------------------------------------------------------------------

def _menu_programmation(app_config, parameter_ctrl: ParameterController) -> None:
    while True:
        print(
            "\n--- PROGRAMMATION ---\n"
            "1) Lire un paramètre ECU\n"
            "2) Écrire un paramètre ECU\n"
            "3) Doc rapide : vocabulaire de codage\n"
            "4) Retour"
        )
        choice = input("> ").strip()
        try:
            if choice == "1":
                name = input("Nom du paramètre : ").strip()
                print(f"{name} = {parameter_ctrl.read(name)}")
            elif choice == "2":
                _handle_write_param(app_config, parameter_ctrl)
            elif choice == "3":
                afficher_doc_codage()
            elif choice == "4":
                return
            else:
                print("Choix invalide.")
        except (SafetyViolation, ParameterError) as exc:
            print(f"Erreur : {exc}")


def _handle_write_param(app_config, parameter_ctrl: ParameterController) -> None:
    name = input("Nom du paramètre : ").strip()
    value = float(input("Nouvelle valeur : ").strip())
    if app_config.interface == "kkl":
        print("⚠️  Vitesse non surveillée sur l'interface KKL : vérifiez vous-même que le véhicule est à l'arrêt.")
    parameter_ctrl.write(name, value, VehicleState())
    print("Paramètre écrit et vérifié.")


# --------------------------------------------------------------------------
# Onglet Internet
# --------------------------------------------------------------------------

def _menu_internet() -> None:
    while True:
        print(
            "\n--- INTERNET ---\n"
            "1) Statut réseau\n"
            "2) Lister les réseaux Wi-Fi disponibles\n"
            "3) Se connecter à un Wi-Fi\n"
            "4) Retour"
        )
        choice = input("> ").strip()
        if choice == "1":
            status = netinfo.get_status()
            print(f"Nom d'hôte : {status.hostname}")
            print(f"Adresses IP : {', '.join(status.ip_addresses) or '(aucune)'}")
            print(f"Accès Internet : {'oui' if status.internet_reachable else 'non'}")
        elif choice == "2":
            networks = netinfo.list_wifi_networks()
            if not networks:
                print("Aucun réseau trouvé (ou nmcli indisponible).")
            for ssid in networks:
                print(f"  {ssid}")
        elif choice == "3":
            ssid = input("SSID : ").strip()
            password = input("Mot de passe : ").strip()
            print(netinfo.connect_wifi(ssid, password))
        elif choice == "4":
            return
        else:
            print("Choix invalide.")


# --------------------------------------------------------------------------
# Onglet Paramètres (réglages de l'application)
# --------------------------------------------------------------------------

def _menu_parametres(app_config: AppConfig, app_config_path: str) -> AppConfig:
    while True:
        print(
            "\n--- PARAMÈTRES ---\n"
            f"1) Interface : {app_config.interface} (obd2 = ELM327/CAN, kkl = câble K-line VAG)\n"
            f"2) Port série : {app_config.port}\n"
            f"3) Vitesse de liaison (baudrate) : {app_config.baudrate}\n"
            f"4) Profil véhicule : {app_config.vehicle_profile_path}\n"
            f"5) Vitesse max autorisée pour actions : {app_config.max_speed_kmh} km/h\n"
            f"6) Confirmation de sécurité obligatoire : {'oui' if app_config.require_confirmation else 'non'}\n"
            f"7) Mode simulation : {'oui' if app_config.simulate else 'non'}\n"
            "8) Enregistrer la configuration\n"
            "9) Retour"
        )
        choice = input("> ").strip()
        if choice == "1":
            value = input(f"Interface ({'/'.join(INTERFACES)}) : ").strip().lower()
            if value in INTERFACES:
                app_config.interface = value
                print("Redémarrez l'application pour appliquer ce changement d'interface.")
            else:
                print("Valeur invalide.")
        elif choice == "2":
            new_port = input("Nouveau port (ex: /dev/ttyUSB0) : ").strip()
            if new_port:
                app_config.port = new_port
            print("Redémarrez l'application pour appliquer ce changement.")
        elif choice == "3":
            value = input("Nouveau baudrate : ").strip()
            if value.isdigit():
                app_config.baudrate = int(value)
                print("Redémarrez l'application pour appliquer ce changement.")
            else:
                print("Valeur invalide.")
        elif choice == "4":
            new_path = input("Chemin du profil véhicule : ").strip()
            if new_path:
                app_config.vehicle_profile_path = new_path
            print("Redémarrez l'application pour charger le nouveau profil.")
        elif choice == "5":
            value = input("Nouvelle vitesse max (km/h) : ").strip()
            try:
                app_config.max_speed_kmh = float(value)
                print("Redémarrez l'application pour appliquer ce changement.")
            except ValueError:
                print("Valeur invalide.")
        elif choice == "6":
            app_config.require_confirmation = not app_config.require_confirmation
            print("Redémarrez l'application pour appliquer ce changement.")
        elif choice == "7":
            app_config.simulate = not app_config.simulate
            print("Redémarrez l'application pour appliquer ce changement.")
        elif choice == "8":
            save_app_config(app_config, app_config_path)
            print(f"Configuration enregistrée dans {app_config_path}.")
        elif choice == "9":
            return app_config
        else:
            print("Choix invalide.")


# --------------------------------------------------------------------------
# Onglet Jeux
# --------------------------------------------------------------------------

def _menu_jeux() -> None:
    while True:
        print(
            "\n--- JEUX ---\n"
            "1) Pendu\n"
            "2) Morpion\n"
            "3) Plus ou moins\n"
            "4) Retour"
        )
        choice = input("> ").strip()
        if choice == "1":
            games.jouer_pendu()
        elif choice == "2":
            games.jouer_morpion()
        elif choice == "3":
            games.jouer_plus_ou_moins()
        elif choice == "4":
            return
        else:
            print("Choix invalide.")
