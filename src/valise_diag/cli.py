"""Menu texte principal à onglets, avec tableau de bord système et petite mise
en scène (démarrage, veille, easter eggs). Fonctionne aussi bien sur un vrai
terminal (clavier direct, veille automatique) qu'en entrée non-interactive
(tests, script) — dans ce dernier cas il retombe sur un menu ligne par ligne
classique plutôt que d'échouer sur un ioctl impossible."""
from __future__ import annotations

import getpass
import os
import select
import sys
import termios
import time
import tty
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from . import (
    dtc_fr,
    easter_eggs,
    games,
    history,
    live_data,
    netinfo,
    netscan,
    pin_lock,
    profiles,
    screensaver,
    session_log,
    system_status,
    system_tools,
)
from .actuators import ActuatorController, ActuatorError
from .boot import show_boot_screen
from .coding_doc import afficher_doc_codage
from .config import AppConfig, INTERFACES, POLICES, VEILLE_TYPES, VehicleProfile, save_app_config
from .dtc import Obd2Client, format_live_value
from .elm327 import PROTOCOLES_TESTABLES, diagnostiquer_port, diagnostiquer_protocoles
from .graphs import boucle_graphiques
from .kwp1281 import KWP1281Client
from .kwp2000 import SID_CLEAR_DIAGNOSTIC_INFORMATION, SID_READ_DTC_BY_STATUS
from .parameters import ParameterController, ParameterError
from .safety import SafetyGuard, SafetyPolicy, SafetyViolation, VehicleState
from .theme import (
    BOLD,
    CYAN,
    GREEN,
    MAGENTA,
    RED,
    RESET,
    YELLOW,
    afficher_bloc_centre,
    boite_titre,
    clear_screen,
    print_centre,
)
from .transport import build_diagnostic_clients, build_kw1281_clients


def _confirm(message: str) -> bool:
    answer = input(f"{message}\nTaper OUI en majuscules pour confirmer : ")
    return answer.strip() == "OUI"


@dataclass
class _MenuContext:
    app_config: AppConfig
    app_config_path: str
    profile: VehicleProfile
    obd2: Optional[Obd2Client]
    actuator_ctrl: ActuatorController
    parameter_ctrl: ParameterController
    uds_clients: Dict[str, object]
    kw1281_clients: Dict[str, KWP1281Client]
    reachable_ecus: Dict[str, object]
    kw1281_ecus: Dict[str, object]
    moniteur: system_status.MoniteurSysteme


def main(app_config: AppConfig, profile: VehicleProfile, app_config_path: str = "config/app.yaml") -> None:
    show_boot_screen(rapide=app_config.boot_rapide)

    if app_config.pin_active and app_config.pin_hash:
        pin_lock.demander_pin(app_config.pin_salt, app_config.pin_hash)

    print_centre(f"{profile.make} {profile.model} {profile.year} — interface {app_config.interface.upper()}", CYAN)
    print_centre("Lisez docs/SECURITE.md avant toute action sur les actionneurs ou les paramètres moteur.", YELLOW)
    time.sleep(1.0)

    guard = SafetyGuard(
        SafetyPolicy(max_speed_kmh=app_config.max_speed_kmh, require_confirmation=app_config.require_confirmation),
        confirm=_confirm,
    )

    uds_clients: Dict[str, object] = {}
    kw1281_clients: Dict[str, KWP1281Client] = {}
    avertissements: List[str] = []
    if not app_config.simulate or app_config.interface == "obd2":
        uds_clients, avert_uds = build_diagnostic_clients(app_config, profile)
        avertissements += avert_uds
    if app_config.interface == "kkl":
        kw1281_clients, avert_kw1281 = build_kw1281_clients(app_config, profile)
        avertissements += avert_kw1281

    reachable_ecus = {ecu.name: ecu for ecu in profile.ecus if ecu.name in uds_clients}
    kw1281_ecus = {ecu.name: ecu for ecu in profile.ecus if ecu.name in kw1281_clients}

    actuator_ctrl = ActuatorController(uds_clients, reachable_ecus, guard)
    parameter_ctrl = ParameterController(uds_clients, reachable_ecus, guard)

    obd2 = None
    if app_config.interface == "obd2" and not app_config.simulate:
        try:
            obd2 = Obd2Client(app_config.port, app_config.baudrate, app_config.protocole_obd2)
        except Exception as exc:  # noqa: BLE001 - matériel externe, jamais une raison de planter le menu
            avertissements.append(f"Connexion OBD2 impossible ({app_config.port}) : {exc}")

    if avertissements:
        print_centre("⚠️  Certains éléments ne sont pas joignables pour l'instant :", YELLOW)
        for avertissement in avertissements:
            print_centre(avertissement, YELLOW)
        print_centre("Le menu reste utilisable ; reconnectez le matériel puis redémarrez si besoin.", CYAN)
        time.sleep(2.0)

    ctx = _MenuContext(
        app_config=app_config,
        app_config_path=app_config_path,
        profile=profile,
        obd2=obd2,
        actuator_ctrl=actuator_ctrl,
        parameter_ctrl=parameter_ctrl,
        uds_clients=uds_clients,
        kw1281_clients=kw1281_clients,
        reachable_ecus=reachable_ecus,
        kw1281_ecus=kw1281_ecus,
        moniteur=system_status.MoniteurSysteme(),
    )

    try:
        _run_top_menu(ctx)
    finally:
        if obd2 is not None:
            obd2.close()


# --------------------------------------------------------------------------
# Tableau de bord et boucle principale
# --------------------------------------------------------------------------

def _afficher_dashboard(ctx: _MenuContext) -> None:
    app_config, profile = ctx.app_config, ctx.profile
    heure = time.strftime("%H:%M:%S")
    # IP et température sont mises en cache par MoniteurSysteme (voir
    # system_status.py) : pas de sous-processus/socket relancé à chaque
    # rafraîchissement du tableau de bord.
    ip = ctx.moniteur.adresse_ip()
    temp = ctx.moniteur.temperature_cpu()
    cpu = ctx.moniteur.cpu_pct()
    ram_u, ram_t, ram_pct = system_status.lire_ram()
    disk_u, disk_t, disk_pct = system_status.lire_disque()
    up_h, up_m = system_status.lire_uptime()
    wifi = system_status.lire_wifi_signal()

    largeur_barre = 40
    lignes = [
        YELLOW + "-" * largeur_barre + RESET,
        YELLOW + f" {heure} | IP {ip} | {app_config.interface.upper()}" + RESET,
        YELLOW + "-" * largeur_barre + RESET,
        GREEN + f" CPU {f'{int(cpu)}%' if cpu is not None else 'N/A'}   "
        f"TEMP {f'{temp:.1f}C' if temp is not None else 'N/A'}" + RESET,
        GREEN + f" RAM {f'{int(ram_u)}/{int(ram_t)}Mo ({int(ram_pct)}%)' if ram_t else 'N/A'}" + RESET,
        GREEN + f" DISQUE {f'{disk_u:.1f}/{disk_t:.1f}Go ({int(disk_pct)}%)' if disk_t else 'N/A'}" + RESET,
        GREEN + f" WIFI {f'{wifi}dBm' if wifi is not None else 'N/A'}   "
        f"UP {f'{up_h}h{up_m}m' if up_h is not None else 'N/A'}" + RESET,
        "",
        *boite_titre(app_config.titre_menu),
        "",
        GREEN + " [1] " + RESET + "Diagnostic",
        GREEN + " [2] " + RESET + "Programmation",
        GREEN + " [3] " + RESET + "Internet",
        GREEN + " [4] " + RESET + "Système",
        GREEN + " [5] " + RESET + "Paramètres",
        GREEN + " [6] " + RESET + "Jeux",
        RED + " [7] " + RESET + "Éteindre le Pi",
        YELLOW + " [8] " + RESET + "Quitter le menu",
        "",
        CYAN + f"{profile.make} {profile.model} {profile.year}" + RESET,
    ]
    afficher_bloc_centre(lignes)


def _dispatch(touche: str, ctx: _MenuContext) -> bool:
    """Exécute l'action associée à la touche. Renvoie False pour quitter le menu principal."""
    if touche == "1":
        _menu_diagnostic(ctx)
    elif touche == "2":
        _menu_programmation(ctx)
    elif touche == "3":
        _menu_internet()
    elif touche == "4":
        _menu_systeme()
    elif touche == "5":
        ctx.app_config = _menu_parametres(ctx.app_config, ctx.app_config_path)
    elif touche == "6":
        _menu_jeux()
    elif touche == "7":
        if _confirm("Éteindre le Raspberry Pi"):
            system_tools.eteindre_pi()
            return False
    elif touche == "8":
        return False
    return True


def _run_top_menu(ctx: _MenuContext) -> None:
    if sys.stdin.isatty():
        _boucle_interactive(ctx)
    else:
        _boucle_simple(ctx)


def _boucle_simple(ctx: _MenuContext) -> None:
    """Repli utilisé quand l'entrée standard n'est pas un vrai terminal (tests,
    pipe) : pas de veille ni de frappe instantanée, un menu classique suffit."""
    while True:
        _afficher_dashboard(ctx)
        touche = input(GREEN + "> " + RESET).strip()
        if not _dispatch(touche, ctx):
            return


def _boucle_interactive(ctx: _MenuContext) -> None:
    fd = sys.stdin.fileno()
    reglages_normaux = termios.tcgetattr(fd)
    secret = ""
    dernier_input = time.time()
    try:
        tty.setcbreak(fd)
        while True:
            _afficher_dashboard(ctx)
            pret, _, _ = select.select([sys.stdin], [], [], 1.0)
            # Lecture directe sur le descripteur de fichier, pas sys.stdin.read() :
            # le TextIOWrapper de sys.stdin bufferise en interne, et un octet "en
            # trop" (ex: le \n tapé après une touche) peut rester coincé dans ce
            # buffer Python sans que le flush termios (TCSAFLUSH) ne le voie — il
            # vole alors la lecture suivante. os.read() n'a pas ce problème.
            touche = os.read(fd, 1).decode(errors="replace") if pret else None

            if touche is None:
                app_config = ctx.app_config
                if app_config.veille_active and time.time() - dernier_input > app_config.veille_delai:
                    # Pas de retour en mode "normal" ici : la veille lit le clavier
                    # sans bloquer (via select), ce qui a besoin du mode cbreak déjà
                    # actif. Y basculer en mode ligne avant l'appel forçait à taper
                    # une touche PUIS Entrée pour en sortir.
                    screensaver.ecran_veille(app_config.veille_type)
                    dernier_input = time.time()
                continue
            dernier_input = time.time()

            secret = (secret + touche)[-10:]
            if secret.endswith("serpent"):
                termios.tcsetattr(fd, termios.TCSADRAIN, reglages_normaux)
                games.jouer_serpent()
                tty.setcbreak(fd)
                secret = ""
                dernier_input = time.time()
                continue
            if secret.endswith("hack"):
                termios.tcsetattr(fd, termios.TCSADRAIN, reglages_normaux)
                easter_eggs.sequence_piratage()
                tty.setcbreak(fd)
                secret = ""
                dernier_input = time.time()
                continue

            termios.tcsetattr(fd, termios.TCSADRAIN, reglages_normaux)
            continuer = _dispatch(touche, ctx)
            tty.setcbreak(fd)
            dernier_input = time.time()
            if not continuer:
                return
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, reglages_normaux)


# --------------------------------------------------------------------------
# Onglet Diagnostic
# --------------------------------------------------------------------------

def _menu_diagnostic(ctx: _MenuContext) -> None:
    while True:
        lignes = boite_titre("DIAGNOSTIC", MAGENTA, CYAN) + [
            "",
            GREEN + " [1] " + RESET + "Lire les codes défauts",
            GREEN + " [2] " + RESET + "Effacer les codes défauts",
            GREEN + " [3] " + RESET + "Lecture temps réel",
            GREEN + " [4] " + RESET + "Graphiques temps réel",
            GREEN + " [5] " + RESET + "Tester un actionneur",
            GREEN + " [6] " + RESET + "Identification ECU",
            GREEN + " [7] " + RESET + "Historique des actions",
            GREEN + " [8] " + RESET + "Enregistrer une session (CSV)",
            GREEN + " [9] " + RESET + "Reconnecter l'adaptateur",
            GREEN + " [10] " + RESET + "Diagnostic bas niveau adaptateur",
            YELLOW + " [11] " + RESET + "Retour",
            "",
        ]
        afficher_bloc_centre(lignes)
        choice = input(GREEN + "> " + RESET).strip()
        try:
            if choice == "1":
                _handle_read_dtc(ctx)
            elif choice == "2":
                _handle_clear_dtc(ctx)
            elif choice == "3":
                _handle_live_data(ctx)
            elif choice == "4":
                _handle_graphiques(ctx)
            elif choice == "5":
                _handle_actuator(ctx)
            elif choice == "6":
                _handle_identification(ctx)
            elif choice == "7":
                _handle_history()
            elif choice == "8":
                _handle_session_log(ctx)
            elif choice == "9":
                _handle_reconnexion(ctx)
            elif choice == "10":
                _handle_diagnostic_bas_niveau(ctx)
            elif choice == "11":
                return
            else:
                print(RED + "Choix invalide." + RESET)
                input("Appuyez sur Entrée pour continuer...")
        except (SafetyViolation, ActuatorError) as exc:
            print(RED + f"Erreur : {exc}" + RESET)
            input("Appuyez sur Entrée pour continuer...")


def _verifier_connexion_vehicule(obd2: Obd2Client) -> bool:
    """Le port série peut s'ouvrir sans que l'adaptateur ni le véhicule ne
    répondent pour autant — sinon "aucun code défaut" ou une valeur
    "non disponible" ressemblent à un résultat normal alors qu'il n'y a tout
    simplement pas eu de dialogue avec l'ECU."""
    if obd2.is_connected():
        return True
    print(RED + "Aucun dialogue établi avec le véhicule." + RESET)
    print("Vérifiez le contact et le branchement, puis utilisez Diagnostic >")
    print("Diagnostic bas niveau adaptateur pour savoir si le problème vient de")
    print("l'adaptateur lui-même ou du véhicule (Reconnecter l'adaptateur ensuite).")
    input("\nAppuyez sur Entrée pour continuer...")
    return False


def _handle_reconnexion(ctx: _MenuContext) -> None:
    if ctx.app_config.interface != "obd2":
        print("Reconnexion disponible uniquement sur l'interface OBD2.")
        input("\nAppuyez sur Entrée pour continuer...")
        return
    if ctx.obd2 is not None:
        ctx.obd2.close()
    print(CYAN + "Nouvelle tentative de connexion..." + RESET)
    try:
        ctx.obd2 = Obd2Client(ctx.app_config.port, ctx.app_config.baudrate, ctx.app_config.protocole_obd2)
    except Exception as exc:  # noqa: BLE001 - matériel externe, jamais une raison de planter le menu
        print(RED + f"Échec : {exc}" + RESET)
        ctx.obd2 = None
        input("\nAppuyez sur Entrée pour continuer...")
        return
    if ctx.obd2.is_connected():
        print(GREEN + "Connexion au véhicule établie." + RESET)
    else:
        print(YELLOW + "Toujours aucun dialogue avec le véhicule — essayez "
              "'Diagnostic bas niveau adaptateur' pour en savoir plus." + RESET)
    input("\nAppuyez sur Entrée pour continuer...")


def _handle_diagnostic_bas_niveau(ctx: _MenuContext) -> None:
    """Sonde le port série directement (AT brut), sans passer par python-obd,
    pour distinguer un adaptateur qui ne répond pas du tout d'un véhicule qui
    ne répond pas malgré un adaptateur fonctionnel."""
    if ctx.app_config.interface != "obd2":
        print("Disponible uniquement sur l'interface OBD2 (adaptateur ELM327).")
        input("\nAppuyez sur Entrée pour continuer...")
        return

    # Libère le port avant de le sonder directement : ctx.obd2 (python-obd)
    # le garde ouvert, et deux connexions simultanées sur le même port
    # brouilleraient les réponses des deux côtés.
    if ctx.obd2 is not None:
        ctx.obd2.close()
        ctx.obd2 = None

    print(CYAN + f"Sondage direct de {ctx.app_config.port} (sans passer par l'appli)..." + RESET)
    resultat = diagnostiquer_port(ctx.app_config.port, ctx.app_config.baudrate)

    if resultat.erreur_ouverture:
        print(RED + f"Impossible d'ouvrir le port : {resultat.erreur_ouverture}" + RESET)
        input("\nAppuyez sur Entrée pour continuer...")
        return

    print(f"ATZ   -> {resultat.reponse_atz.strip() or '(vide)'}")
    print(f"ATSP0 -> {resultat.reponse_atsp0.strip() or '(vide)'}")
    print(f"0100  -> {resultat.reponse_0100.strip() or '(vide)'}")
    print()
    if not resultat.adaptateur_repond:
        print(RED + "L'adaptateur ne répond pas : vérifiez le port, le débit (baudrate) et le câble." + RESET)
        print(CYAN + "\nUtilisez 'Reconnecter l'adaptateur' ensuite pour rétablir la connexion normale." + RESET)
        input("\nAppuyez sur Entrée pour continuer...")
        return
    elif not resultat.vehicule_repond:
        print(YELLOW + "Adaptateur OK, mais le véhicule ne répond pas en négociation automatique (ATSP0)." + RESET)
        print("Certains adaptateurs (notamment les clones bon marché) négocient mal le protocole")
        print("automatiquement. Test de chaque protocole un par un (quelques secondes)...")
        resultats_protocoles = diagnostiquer_protocoles(ctx.app_config.port, ctx.app_config.baudrate)
        fonctionnels = []
        for r in resultats_protocoles:
            statut = GREEN + "OK" + RESET if r.fonctionne else RED + "--" + RESET
            print(f"  ATSP{r.code} ({r.libelle}) : {statut}")
            if r.fonctionne:
                fonctionnels.append(r)
        if fonctionnels:
            meilleur = fonctionnels[0]
            print(GREEN + f"\nLe protocole ATSP{meilleur.code} ({meilleur.libelle}) fonctionne !" + RESET)
            print("Le véhicule répond bien : le souci vient de l'auto-négociation de l'adaptateur,")
            print("pas du véhicule ni du câblage.")
            if _confirm(f"Forcer ce protocole (ATSP{meilleur.code}) pour cet adaptateur à l'avenir"):
                ctx.app_config.protocole_obd2 = meilleur.code
                save_app_config(ctx.app_config, ctx.app_config_path)
                print(GREEN + "Enregistré. Utilisez 'Reconnecter l'adaptateur' pour l'appliquer." + RESET)
        else:
            print(RED + "\nAucun protocole ne répond : le véhicule ne dialogue pas." + RESET)
            print("Vérifications physiques avant de suspecter l'adaptateur lui-même :")
            print("  - contact mis (pas juste les warnings, le tableau de bord complet allumé)")
            print("  - le connecteur OBD est enfoncé jusqu'au bout, rien ne bouge une fois en place")
            print("  - la diode de l'adaptateur s'allume au branchement (signe qu'il reçoit du +12V)")
            print("  - pas de broches tordues/corrodées dans le connecteur OBD du véhicule")
            print("Si tout est correct malgré ça, l'adaptateur (pas seulement son auto-négociation)")
            print("est probablement en cause : essayez-le sur un autre véhicule si possible pour trancher.")
    else:
        print(GREEN + "Adaptateur et véhicule répondent correctement." + RESET)
    print(CYAN + "\nUtilisez 'Reconnecter l'adaptateur' ensuite pour rétablir la connexion normale." + RESET)
    input("\nAppuyez sur Entrée pour continuer...")


def _handle_read_dtc(ctx: _MenuContext) -> None:
    app_config = ctx.app_config
    if app_config.interface == "obd2":
        if ctx.obd2 is None:
            print("Non disponible en mode simulation.")
            input("\nAppuyez sur Entrée pour continuer...")
        elif _verifier_connexion_vehicule(ctx.obd2):
            dtcs = ctx.obd2.read_dtcs()
            if not dtcs:
                print("Aucun code défaut.")
            for dtc in dtcs:
                print(f"{dtc.code}: {dtc_fr.decrire(dtc.code, dtc.description)}")
            input("\nAppuyez sur Entrée pour continuer...")
        return

    for name, client in ctx.uds_clients.items():
        if ctx.reachable_ecus[name].protocol != "kwp2000_kline":
            continue
        try:
            raw = client.request(SID_READ_DTC_BY_STATUS, bytes([0x00]))
            print(f"[{name}] codes défauts (hex brut, non décodé) : {raw.hex(' ')}")
        except Exception as exc:  # noqa: BLE001 - surfaced to the operator, not swallowed
            print(f"[{name}] erreur : {exc}")
    for name, client in ctx.kw1281_clients.items():
        block_title = ctx.kw1281_ecus[name].kw1281_blocks.get("read_fault_codes")
        if block_title is None:
            print(f"[{name}] 'read_fault_codes' non défini dans le profil (section blocks:).")
            continue
        try:
            response = client.request(block_title)
            print(f"[{name}] codes défauts (hex brut, non décodé) : {response.data.hex(' ')}")
        except Exception as exc:  # noqa: BLE001
            print(f"[{name}] erreur : {exc}")
    input("\nAppuyez sur Entrée pour continuer...")


def _handle_clear_dtc(ctx: _MenuContext) -> None:
    if not _confirm("Confirmer l'effacement des codes défauts"):
        return
    app_config = ctx.app_config
    if app_config.interface == "obd2":
        if ctx.obd2 is None:
            print("Non disponible en mode simulation.")
            input("\nAppuyez sur Entrée pour continuer...")
        elif _verifier_connexion_vehicule(ctx.obd2):
            ctx.obd2.clear_dtcs()
            print("Codes défauts effacés.")
            history.log_event(f"Codes défauts effacés (OBD2, {ctx.profile.make} {ctx.profile.model})")
            input("\nAppuyez sur Entrée pour continuer...")
        return

    for name, client in ctx.uds_clients.items():
        if ctx.reachable_ecus[name].protocol != "kwp2000_kline":
            continue
        try:
            client.request(SID_CLEAR_DIAGNOSTIC_INFORMATION, bytes([0xFF, 0x00]))
            print(f"[{name}] codes défauts effacés.")
            history.log_event(f"Codes défauts effacés ({name}, KWP2000)")
        except Exception as exc:  # noqa: BLE001
            print(f"[{name}] erreur : {exc}")
    for name, client in ctx.kw1281_clients.items():
        block_title = ctx.kw1281_ecus[name].kw1281_blocks.get("clear_fault_codes")
        if block_title is None:
            print(f"[{name}] 'clear_fault_codes' non défini dans le profil (section blocks:).")
            continue
        try:
            client.request(block_title)
            print(f"[{name}] codes défauts effacés.")
            history.log_event(f"Codes défauts effacés ({name}, KW1281)")
        except Exception as exc:  # noqa: BLE001
            print(f"[{name}] erreur : {exc}")
    input("\nAppuyez sur Entrée pour continuer...")


def _handle_live_data(ctx: _MenuContext) -> None:
    if ctx.app_config.interface != "obd2":
        print("Lecture temps réel : utilisez Programmation > Lire un paramètre ECU "
              "(les valeurs temps réel KKL sont définies comme des paramètres dans le profil véhicule).")
        input("\nAppuyez sur Entrée pour continuer...")
        return
    if ctx.obd2 is None:
        print("Non disponible en mode simulation.")
        input("\nAppuyez sur Entrée pour continuer...")
        return
    if not _verifier_connexion_vehicule(ctx.obd2):
        return

    while True:
        lignes = boite_titre("LECTURE TEMPS REEL", MAGENTA, CYAN) + [""]
        categories = live_data.categories()
        for i, categorie in enumerate(categories, start=1):
            lignes.append(GREEN + f" [{i}] " + RESET + categorie)
        lignes.append(GREEN + f" [{len(categories) + 1}] " + RESET + "Tout afficher")
        lignes.append(YELLOW + f" [{len(categories) + 2}] " + RESET + "Retour")
        lignes.append("")
        afficher_bloc_centre(lignes)
        choice = input(GREEN + "> " + RESET).strip()

        if choice == str(len(categories) + 2):
            return
        if choice == str(len(categories) + 1):
            _afficher_valeurs(ctx.obd2, live_data.all_commands())
            continue
        if choice.isdigit() and 1 <= int(choice) <= len(categories):
            _afficher_valeurs(ctx.obd2, live_data.commands_for(categories[int(choice) - 1]))
            continue
        print(RED + "Choix invalide." + RESET)
        input("Appuyez sur Entrée pour continuer...")


def _handle_graphiques(ctx: _MenuContext) -> None:
    if ctx.app_config.interface != "obd2":
        print("Graphiques disponibles uniquement sur l'interface OBD2.")
        input("\nAppuyez sur Entrée pour continuer...")
        return
    if ctx.obd2 is None:
        print("Non disponible en mode simulation.")
        input("\nAppuyez sur Entrée pour continuer...")
        return
    if not _verifier_connexion_vehicule(ctx.obd2):
        return
    print(CYAN + "Il n'existe pas de PID OBD-II standard pour la puissance moteur (ça se" + RESET)
    print(CYAN + "mesure sur un banc) : régime et charge moteur servent de proxys de tendance." + RESET)
    input("Appuyez sur Entrée pour lancer les graphiques...")
    boucle_graphiques(ctx.obd2)


def _afficher_valeurs(obd2: Obd2Client, commandes: List[Tuple[str, str]]) -> None:
    clear_screen()
    for command_name, label in commandes:
        valeur = format_live_value(obd2.live_value(command_name))
        print(f"{label} : {valeur}")
    input("\nAppuyez sur Entrée pour continuer...")


def _handle_actuator(ctx: _MenuContext) -> None:
    name = input("Nom de l'actionneur : ").strip()
    if ctx.app_config.interface == "kkl":
        print(YELLOW + "⚠️  Vitesse non surveillée sur l'interface KKL : "
              "vérifiez vous-même que le véhicule est à l'arrêt." + RESET)
    state = ctx.obd2.vehicle_state() if ctx.obd2 else VehicleState()
    ctx.actuator_ctrl.activate(name, state)
    print(GREEN + "Test terminé, contrôle rendu à l'ECU." + RESET)
    history.log_event(f"Test actionneur '{name}' ({ctx.app_config.interface})")
    input("\nAppuyez sur Entrée pour continuer...")


def _handle_identification(ctx: _MenuContext) -> None:
    if ctx.app_config.interface == "obd2" and ctx.obd2 is not None:
        vin = ctx.obd2.live_value("VIN")
        if vin:
            print(f"VIN : {vin}")
    for name, ecu in {**ctx.reachable_ecus, **ctx.kw1281_ecus}.items():
        print(f"{name}: protocole={ecu.protocol}, adresse={ecu.tx_header}")
    input("\nAppuyez sur Entrée pour continuer...")


def _handle_history() -> None:
    lignes = history.read_recent(20)
    print(CYAN + BOLD + "=== HISTORIQUE DES ACTIONS ===" + RESET + "\n")
    if not lignes:
        print(YELLOW + "Aucune action enregistrée." + RESET)
    for ligne in lignes:
        print(GREEN + ligne + RESET)
    input("\nAppuyez sur Entrée pour continuer...")


def _handle_session_log(ctx: _MenuContext) -> None:
    if ctx.app_config.interface != "obd2":
        print("Enregistrement de session : disponible uniquement sur l'interface OBD2 pour le moment.")
        input("\nAppuyez sur Entrée pour continuer...")
        return
    if ctx.obd2 is None:
        print("Non disponible en mode simulation.")
        input("\nAppuyez sur Entrée pour continuer...")
        return
    if not _verifier_connexion_vehicule(ctx.obd2):
        return

    categories = live_data.categories()
    print("Quelles valeurs enregistrer ?")
    for i, categorie in enumerate(categories, start=1):
        print(f"  [{i}] {categorie}")
    print(f"  [{len(categories) + 1}] Tout")
    choix = input(GREEN + "> " + RESET).strip()
    if choix == str(len(categories) + 1):
        commandes = live_data.all_commands()
    elif choix.isdigit() and 1 <= int(choix) <= len(categories):
        commandes = live_data.commands_for(categories[int(choix) - 1])
    else:
        print(RED + "Choix invalide." + RESET)
        input("Appuyez sur Entrée pour continuer...")
        return

    try:
        duree_s = float(input("Durée en secondes (0 = jusqu'à Ctrl+C) : ").strip())
    except ValueError:
        print(RED + "Valeur invalide." + RESET)
        input("Appuyez sur Entrée pour continuer...")
        return

    print(CYAN + "Enregistrement en cours (Ctrl+C pour arrêter)..." + RESET)

    def afficher_avancement(tick: int) -> None:
        sys.stdout.write(f"\r  {tick} mesure(s) enregistrée(s)...")
        sys.stdout.flush()

    chemin = session_log.enregistrer(ctx.obd2, commandes, duree_s, sur_tick=afficher_avancement)
    print()
    print(GREEN + f"Session enregistrée dans {chemin}" + RESET)
    history.log_event(f"Session CSV enregistrée : {chemin}")
    input("\nAppuyez sur Entrée pour continuer...")


# --------------------------------------------------------------------------
# Onglet Programmation
# --------------------------------------------------------------------------

def _menu_programmation(ctx: _MenuContext) -> None:
    while True:
        lignes = boite_titre("PROGRAMMATION", CYAN, MAGENTA) + [
            "",
            GREEN + " [1] " + RESET + "Lire un paramètre ECU",
            GREEN + " [2] " + RESET + "Écrire un paramètre ECU",
            GREEN + " [3] " + RESET + "Doc rapide : vocabulaire de codage",
            YELLOW + " [4] " + RESET + "Retour",
            "",
        ]
        afficher_bloc_centre(lignes)
        choice = input(GREEN + "> " + RESET).strip()
        try:
            if choice == "1":
                name = input("Nom du paramètre : ").strip()
                print(f"{name} = {ctx.parameter_ctrl.read(name)}")
                input("\nAppuyez sur Entrée pour continuer...")
            elif choice == "2":
                _handle_write_param(ctx)
            elif choice == "3":
                clear_screen()
                afficher_doc_codage()
                input("\nAppuyez sur Entrée pour continuer...")
            elif choice == "4":
                return
            else:
                print(RED + "Choix invalide." + RESET)
                input("Appuyez sur Entrée pour continuer...")
        except (SafetyViolation, ParameterError) as exc:
            print(RED + f"Erreur : {exc}" + RESET)
            input("Appuyez sur Entrée pour continuer...")


def _handle_write_param(ctx: _MenuContext) -> None:
    name = input("Nom du paramètre : ").strip()
    value = float(input("Nouvelle valeur : ").strip())
    if ctx.app_config.interface == "kkl":
        print(YELLOW + "⚠️  Vitesse non surveillée sur l'interface KKL : "
              "vérifiez vous-même que le véhicule est à l'arrêt." + RESET)
    ctx.parameter_ctrl.write(name, value, VehicleState())
    print(GREEN + "Paramètre écrit et vérifié." + RESET)
    history.log_event(f"Paramètre '{name}' = {value} ({ctx.app_config.interface})")
    input("\nAppuyez sur Entrée pour continuer...")


# --------------------------------------------------------------------------
# Onglet Système (outils Raspberry Pi — distinct de Programmation/ECU)
# --------------------------------------------------------------------------

def _menu_systeme() -> None:
    while True:
        lignes = boite_titre("SYSTEME", GREEN, CYAN) + [
            "",
            GREEN + " [1] " + RESET + "Terminal libre (bash)",
            GREEN + " [2] " + RESET + "Console Python interactive",
            GREEN + " [3] " + RESET + "Éditer un fichier (nano)",
            GREEN + " [4] " + RESET + "Informations système",
            GREEN + " [5] " + RESET + "Mettre à jour le système (apt)",
            YELLOW + " [6] " + RESET + "Retour",
            "",
        ]
        afficher_bloc_centre(lignes)
        choice = input(GREEN + "> " + RESET).strip()
        if choice == "1":
            clear_screen()
            print(CYAN + "Terminal libre. Tapez 'exit' pour revenir." + RESET)
            system_tools.ouvrir_shell()
        elif choice == "2":
            clear_screen()
            print(CYAN + "Console Python. Tapez exit() pour revenir." + RESET)
            system_tools.ouvrir_python_repl()
        elif choice == "3":
            nom = input("Nom du fichier : ").strip()
            if nom:
                system_tools.editer_fichier(nom)
        elif choice == "4":
            clear_screen()
            print(system_tools.infos_systeme())
            input("\nAppuyez sur Entrée pour continuer...")
        elif choice == "5":
            confirme = input("Lancer la mise à jour ? (oui/non) : ").strip().lower() == "oui"
            system_tools.mettre_a_jour_systeme(confirme)
            input("\nAppuyez sur Entrée pour continuer...")
        elif choice == "6":
            return
        else:
            print(RED + "Choix invalide." + RESET)
            input("Appuyez sur Entrée pour continuer...")


# --------------------------------------------------------------------------
# Onglet Internet
# --------------------------------------------------------------------------

def _menu_internet() -> None:
    while True:
        lignes = boite_titre("INTERNET", CYAN, MAGENTA) + [
            "",
            GREEN + " [1] " + RESET + "Statut réseau",
            GREEN + " [2] " + RESET + "Lister les réseaux Wi-Fi",
            GREEN + " [3] " + RESET + "Se connecter à un Wi-Fi",
            GREEN + " [4] " + RESET + "Configuration Wi-Fi avancée (nmtui)",
            GREEN + " [5] " + RESET + "Ping une adresse",
            GREEN + " [6] " + RESET + "Test de débit",
            GREEN + " [7] " + RESET + "Naviguer",
            GREEN + " [8] " + RESET + "Scanner réseau",
            YELLOW + " [9] " + RESET + "Retour",
            "",
        ]
        afficher_bloc_centre(lignes)
        choice = input(GREEN + "> " + RESET).strip()
        if choice == "1":
            status = netinfo.get_status()
            print(f"Nom d'hôte : {status.hostname}")
            print(f"Adresses IP : {', '.join(status.ip_addresses) or '(aucune)'}")
            print(f"Accès Internet : {'oui' if status.internet_reachable else 'non'}")
            input("\nAppuyez sur Entrée pour continuer...")
        elif choice == "2":
            networks = netinfo.list_wifi_networks()
            if not networks:
                print("Aucun réseau trouvé (ou nmcli indisponible).")
            for ssid in networks:
                print(f"  {ssid}")
            input("\nAppuyez sur Entrée pour continuer...")
        elif choice == "3":
            ssid = input("SSID : ").strip()
            password = input("Mot de passe : ").strip()
            print(netinfo.connect_wifi(ssid, password))
            input("\nAppuyez sur Entrée pour continuer...")
        elif choice == "4":
            netinfo.ouvrir_configuration_wifi()
        elif choice == "5":
            cible = input("Adresse ou nom de domaine à pinger : ").strip()
            if cible:
                clear_screen()
                netinfo.ping_anime(cible)
                input("\nAppuyez sur Entrée pour continuer...")
        elif choice == "6":
            clear_screen()
            print(CYAN + "Mesure du débit en cours..." + RESET)
            mbps = netinfo.mesurer_debit()
            if mbps is None:
                print(RED + "Impossible de mesurer le débit (vérifiez la connexion)." + RESET)
            else:
                print(GREEN + f"Débit mesuré : {mbps:.1f} Mbps" + RESET)
                print(YELLOW + netinfo.commentaire_debit(mbps) + RESET)
            input("\nAppuyez sur Entrée pour continuer...")
        elif choice == "7":
            _handle_navigation()
        elif choice == "8":
            _menu_scanner_reseau()
        elif choice == "9":
            return
        else:
            print(RED + "Choix invalide." + RESET)
            input("Appuyez sur Entrée pour continuer...")


def _handle_navigation() -> None:
    print("1) DuckDuckGo\n2) Wikipédia\n3) Saisir une URL")
    choix = input(GREEN + "> " + RESET).strip()
    if choix == "1":
        netinfo.naviguer("lite.duckduckgo.com")
    elif choix == "2":
        netinfo.naviguer("fr.wikipedia.org")
    elif choix == "3":
        url = input("URL (sans https://) : ").strip()
        if url:
            netinfo.naviguer(url)


def _menu_scanner_reseau() -> None:
    while True:
        lignes = boite_titre("SCANNER RESEAU", RED, CYAN) + [
            "",
            GREEN + " [1] " + RESET + "Découverte des hôtes (qui est sur le réseau)",
            GREEN + " [2] " + RESET + "Scan rapide (ports courants)",
            GREEN + " [3] " + RESET + "Scan standard (ports + services)",
            GREEN + " [4] " + RESET + "Scan complet (tous les ports, lent)",
            GREEN + " [5] " + RESET + "Scan personnalisé (ports au choix)",
            GREEN + " [6] " + RESET + "Consulter les rapports enregistrés",
            YELLOW + " [7] " + RESET + "Retour",
            "",
        ]
        afficher_bloc_centre(lignes)
        choice = input(GREEN + "> " + RESET).strip()
        if choice == "1":
            _handle_decouverte_hotes()
        elif choice == "2":
            _handle_scan("Scan rapide", netscan.scan_rapide)
        elif choice == "3":
            _handle_scan("Scan standard", netscan.scan_standard)
        elif choice == "4":
            _handle_scan(
                "Scan complet",
                netscan.scan_complet,
                avertissement="Peut prendre plusieurs dizaines de minutes sur les 65535 ports.",
            )
        elif choice == "5":
            _handle_scan_personnalise()
        elif choice == "6":
            _handle_rapports_scan()
        elif choice == "7":
            return
        else:
            print(RED + "Choix invalide." + RESET)
            input("Appuyez sur Entrée pour continuer...")


def _handle_decouverte_hotes() -> None:
    suggestion = netscan.deviner_sous_reseau()
    invite = f"Sous-réseau à scanner (Entrée pour {suggestion}) : " if suggestion else "Sous-réseau à scanner (ex: 192.168.1.0/24) : "
    cible = input(invite).strip() or suggestion
    if not cible:
        print(RED + "Aucune cible fournie." + RESET)
        input("Appuyez sur Entrée pour continuer...")
        return
    print(CYAN + f"Découverte des hôtes sur {cible} en cours..." + RESET)
    try:
        resultat = netscan.decouverte_hotes(cible)
    except netscan.ErreurScan as exc:
        print(RED + f"Erreur : {exc}" + RESET)
        input("Appuyez sur Entrée pour continuer...")
        return
    _afficher_resultat_scan(resultat, avec_ports=False)


def _handle_scan(titre: str, fonction_scan, avertissement: str = "") -> None:
    cible = input("Cible (IP, nom d'hôte ou plage, ex: 192.168.1.10) : ").strip()
    if not cible:
        print(RED + "Aucune cible fournie." + RESET)
        input("Appuyez sur Entrée pour continuer...")
        return
    if avertissement:
        print(YELLOW + avertissement + RESET)
        if not _confirm(f"{titre} sur {cible}"):
            return
    print(CYAN + f"{titre} sur {cible} en cours..." + RESET)
    try:
        resultat = fonction_scan(cible)
    except netscan.ErreurScan as exc:
        print(RED + f"Erreur : {exc}" + RESET)
        input("Appuyez sur Entrée pour continuer...")
        return
    _afficher_resultat_scan(resultat)


def _handle_scan_personnalise() -> None:
    cible = input("Cible (IP ou nom d'hôte) : ").strip()
    ports = input("Ports (ex: 22,80,443 ou 1-1024) : ").strip()
    if not cible or not ports:
        print(RED + "Cible et ports requis." + RESET)
        input("Appuyez sur Entrée pour continuer...")
        return
    print(CYAN + f"Scan de {cible} (ports {ports}) en cours..." + RESET)
    try:
        resultat = netscan.scan_personnalise(cible, ports)
    except netscan.ErreurScan as exc:
        print(RED + f"Erreur : {exc}" + RESET)
        input("Appuyez sur Entrée pour continuer...")
        return
    _afficher_resultat_scan(resultat)


def _afficher_resultat_scan(resultat, avec_ports: bool = True) -> None:
    print()
    if not resultat.hotes:
        print(YELLOW + "Aucun hôte trouvé." + RESET)
    for hote in resultat.hotes:
        if hote.etat != "up":
            continue
        print(GREEN + f"{hote.ip}" + RESET + (f" ({hote.nom})" if hote.nom else "") + f" — {hote.etat}")
        if avec_ports:
            ports_ouverts = [p for p in hote.ports if p.etat == "open"]
            if not ports_ouverts:
                print("    (aucun port ouvert parmi ceux scannés)")
            for port in ports_ouverts:
                extra = f" — {port.version}" if port.version else ""
                print(f"    {port.numero}/{port.protocole}  {port.service}{extra}")
    chemin = netscan.enregistrer_rapport(resultat)
    history.log_event(f"Scan réseau : {resultat.commande}")
    print(GREEN + f"\nRapport enregistré dans {chemin}" + RESET)
    input("\nAppuyez sur Entrée pour continuer...")


def _handle_rapports_scan() -> None:
    rapports = netscan.lister_rapports()
    if not rapports:
        print(YELLOW + "Aucun rapport enregistré." + RESET)
        input("\nAppuyez sur Entrée pour continuer...")
        return
    for i, chemin in enumerate(rapports[:20], start=1):
        print(f"  [{i}] {chemin.name}")
    choix = input("Numéro du rapport à afficher (Entrée pour revenir) : ").strip()
    if choix.isdigit() and 1 <= int(choix) <= len(rapports):
        print()
        print(rapports[int(choix) - 1].read_text(encoding="utf-8"))
        input("\nAppuyez sur Entrée pour continuer...")


# --------------------------------------------------------------------------
# Onglet Paramètres (application + apparence + PIN)
# --------------------------------------------------------------------------

def _menu_parametres(app_config: AppConfig, app_config_path: str) -> AppConfig:
    while True:
        lignes = boite_titre("PARAMETRES", MAGENTA, CYAN) + [
            "",
            GREEN + " [1] " + RESET + f"Interface : {app_config.interface}",
            GREEN + " [2] " + RESET + f"Port série : {app_config.port}",
            GREEN + " [3] " + RESET + f"Baudrate : {app_config.baudrate}",
            GREEN + " [4] " + RESET + f"Protocole ELM327 : {app_config.protocole_obd2}",
            GREEN + " [5] " + RESET + f"Profil véhicule : {app_config.vehicle_profile_path}",
            GREEN + " [6] " + RESET + f"Vitesse max autorisée : {app_config.max_speed_kmh} km/h",
            GREEN + " [7] " + RESET + f"Confirmation de sécurité : {_oui_non(app_config.require_confirmation)}",
            GREEN + " [8] " + RESET + f"Mode simulation : {_oui_non(app_config.simulate)}",
            GREEN + " [9] " + RESET + f"Titre du menu : {app_config.titre_menu}",
            GREEN + " [10] " + RESET + f"Écran de veille : {_oui_non(app_config.veille_active)}",
            GREEN + " [11] " + RESET + f"Délai avant veille : {app_config.veille_delai}s",
            GREEN + " [12] " + RESET + f"Type de veille : {app_config.veille_type}",
            GREEN + " [13] " + RESET + f"Taille de police console : {app_config.police}",
            GREEN + " [14] " + RESET + f"Démarrage automatique : {_oui_non(app_config.autostart)}",
            GREEN + " [15] " + RESET + f"Démarrage rapide : {_oui_non(app_config.boot_rapide)}",
            GREEN + " [16] " + RESET + f"Code PIN : {_oui_non(app_config.pin_active)}",
            GREEN + " [17] " + RESET + "Enregistrer la configuration",
            GREEN + " [18] " + RESET + "Réinitialiser tous les paramètres",
            YELLOW + " [19] " + RESET + "Retour",
            "",
        ]
        afficher_bloc_centre(lignes)
        choice = input(GREEN + "> " + RESET).strip()

        if choice == "1":
            value = input(f"Interface ({'/'.join(INTERFACES)}) : ").strip().lower()
            if value in INTERFACES:
                app_config.interface = value
                _redemarrage_requis()
            else:
                print(RED + "Valeur invalide." + RESET)
        elif choice == "2":
            new_port = input("Nouveau port (ex: /dev/ttyUSB0) : ").strip()
            if new_port:
                app_config.port = new_port
                _redemarrage_requis()
        elif choice == "3":
            value = input("Nouveau baudrate : ").strip()
            if value.isdigit():
                app_config.baudrate = int(value)
                _redemarrage_requis()
            else:
                print(RED + "Valeur invalide." + RESET)
        elif choice == "4":
            codes_valides = ["AUTO"] + [code for code, _ in PROTOCOLES_TESTABLES]
            print("AUTO = négociation automatique par l'adaptateur (par défaut).")
            for code, libelle in PROTOCOLES_TESTABLES:
                print(f"  {code} = {libelle}")
            value = input("Protocole (AUTO ou un des codes ci-dessus) : ").strip().upper()
            if value in codes_valides:
                app_config.protocole_obd2 = value
                _redemarrage_requis()
            else:
                print(RED + "Valeur invalide." + RESET)
        elif choice == "5":
            _menu_profil_vehicule(app_config)
        elif choice == "6":
            value = input("Nouvelle vitesse max (km/h) : ").strip()
            try:
                app_config.max_speed_kmh = float(value)
                _redemarrage_requis()
            except ValueError:
                print(RED + "Valeur invalide." + RESET)
        elif choice == "7":
            app_config.require_confirmation = not app_config.require_confirmation
            _redemarrage_requis()
        elif choice == "8":
            app_config.simulate = not app_config.simulate
            _redemarrage_requis()
        elif choice == "9":
            nouveau = input("Nouveau titre (max 30 caractères) : ").strip()
            if nouveau:
                app_config.titre_menu = nouveau[:30]
        elif choice == "10":
            app_config.veille_active = not app_config.veille_active
        elif choice == "11":
            value = input("Nouveau délai en secondes (10-600) : ").strip()
            if value.isdigit() and 10 <= int(value) <= 600:
                app_config.veille_delai = int(value)
            else:
                print(RED + "Valeur invalide." + RESET)
        elif choice == "12":
            print(f"Choix : {' / '.join(VEILLE_TYPES)}")
            value = input("Type : ").strip().lower()
            if value in VEILLE_TYPES:
                app_config.veille_type = value
            else:
                print(RED + "Choix invalide." + RESET)
        elif choice == "13":
            print(f"Choix : {' / '.join(POLICES)}")
            value = input("Taille : ").strip().lower()
            if value in POLICES:
                app_config.police = value
                if not system_tools.appliquer_police(value):
                    print(RED + "Impossible d'appliquer cette police (fichier absent ?)." + RESET)
            else:
                print(RED + "Choix invalide." + RESET)
        elif choice == "14":
            app_config.autostart = not app_config.autostart
            system_tools.appliquer_autostart(app_config.autostart)
        elif choice == "15":
            app_config.boot_rapide = not app_config.boot_rapide
        elif choice == "16":
            _gerer_pin(app_config)
        elif choice == "17":
            save_app_config(app_config, app_config_path)
            print(GREEN + f"Configuration enregistrée dans {app_config_path}." + RESET)
            input("Appuyez sur Entrée pour continuer...")
        elif choice == "18":
            if input("Tapez 'oui' pour réinitialiser tous les paramètres : ").strip().lower() == "oui":
                defaut = AppConfig()
                app_config.__dict__.update(defaut.__dict__)
                system_tools.appliquer_police(app_config.police)
                system_tools.appliquer_autostart(app_config.autostart)
                print(GREEN + "Paramètres réinitialisés." + RESET)
            input("Appuyez sur Entrée pour continuer...")
        elif choice == "19":
            return app_config
        else:
            print(RED + "Choix invalide." + RESET)


def _oui_non(valeur: bool) -> str:
    return "oui" if valeur else "non"


def _redemarrage_requis() -> None:
    print(YELLOW + "Redémarrez l'application pour appliquer ce changement." + RESET)


def _menu_profil_vehicule(app_config: AppConfig) -> None:
    while True:
        profils = profiles.lister_profils()
        print(f"\nProfil actif : {app_config.vehicle_profile_path}")
        print("1) Taper un chemin personnalisé")
        print("2) Choisir parmi les profils enregistrés" + (f" ({len(profils)})" if profils else " (aucun)"))
        print("3) Enregistrer le profil actif sous un nom")
        print("4) Retour")
        choix = input(GREEN + "> " + RESET).strip()

        if choix == "1":
            new_path = input("Chemin du profil véhicule : ").strip()
            if new_path:
                app_config.vehicle_profile_path = new_path
                _redemarrage_requis()
        elif choix == "2":
            if not profils:
                print(RED + "Aucun profil enregistré (option 3 pour en créer un)." + RESET)
                continue
            for i, nom in enumerate(profils, start=1):
                print(f"  [{i}] {nom}")
            sous_choix = input("Numéro du profil : ").strip()
            if sous_choix.isdigit() and 1 <= int(sous_choix) <= len(profils):
                nom = profils[int(sous_choix) - 1]
                app_config.vehicle_profile_path = str(profiles.chemin_profil(nom))
                _redemarrage_requis()
            else:
                print(RED + "Choix invalide." + RESET)
        elif choix == "3":
            nom = input("Nom à donner à ce profil (ex: Golf de Mathis) : ").strip()
            try:
                destination = profiles.enregistrer_profil_actuel(app_config.vehicle_profile_path, nom)
                print(GREEN + f"Profil enregistré sous {destination}." + RESET)
            except (profiles.NomProfilInvalide, OSError) as exc:
                print(RED + f"Erreur : {exc}" + RESET)
        elif choix == "4":
            return
        else:
            print(RED + "Choix invalide." + RESET)


def _gerer_pin(app_config: AppConfig) -> None:
    if app_config.pin_active:
        sous_choix = input("1) Changer le PIN  2) Désactiver  (autre = annuler) : ").strip()
        if sous_choix == "1":
            _definir_pin(app_config)
        elif sous_choix == "2":
            app_config.pin_active = False
            app_config.pin_hash = ""
            app_config.pin_salt = ""
            print(GREEN + "PIN désactivé." + RESET)
    elif input("Activer un code PIN au démarrage ? (oui/non) : ").strip().lower() == "oui":
        _definir_pin(app_config)
        app_config.pin_active = bool(app_config.pin_hash)
    input("Appuyez sur Entrée pour continuer...")


def _definir_pin(app_config: AppConfig) -> None:
    p1 = getpass.getpass("Nouveau PIN : ")
    p2 = getpass.getpass("Confirmez le PIN : ")
    if p1 and p1 == p2:
        sel = pin_lock.generer_sel()
        app_config.pin_salt = sel
        app_config.pin_hash = pin_lock.hash_pin(p1, sel)
        print(GREEN + "PIN mis à jour." + RESET)
    else:
        print(RED + "Les deux codes ne correspondent pas." + RESET)


# --------------------------------------------------------------------------
# Onglet Jeux
# --------------------------------------------------------------------------

def _menu_jeux() -> None:
    while True:
        lignes = boite_titre("JEUX", YELLOW, GREEN) + [
            "",
            GREEN + " [1] " + RESET + "Pendu",
            GREEN + " [2] " + RESET + "Morpion",
            GREEN + " [3] " + RESET + "Plus ou moins",
            GREEN + " [4] " + RESET + "Serpent",
            YELLOW + " [5] " + RESET + "Retour",
            "",
        ]
        afficher_bloc_centre(lignes)
        choice = input(GREEN + "> " + RESET).strip()
        if choice == "1":
            games.jouer_pendu()
        elif choice == "2":
            games.jouer_morpion()
        elif choice == "3":
            games.jouer_plus_ou_moins()
        elif choice == "4":
            games.jouer_serpent()
        elif choice == "5":
            return
        else:
            print(RED + "Choix invalide." + RESET)
