"""Entry point: `python -m valise_diag --config config/app.yaml`."""
from __future__ import annotations

import argparse
import logging

from .cli import main as cli_main
from .config import load_app_config, load_vehicle_profile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Valise de diagnostic OBD/UDS pour Raspberry Pi")
    parser.add_argument("--config", default="config/app.yaml", help="Fichier de configuration de l'application")
    parser.add_argument("--vehicle-profile", default=None, help="Surcharge le profil véhicule du fichier de config")
    parser.add_argument("--simulate", action="store_true", help="Mode simulation, sans matériel")
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    app_config = load_app_config(args.config)
    if args.simulate:
        app_config.simulate = True

    profile_path = args.vehicle_profile or app_config.vehicle_profile_path
    profile = load_vehicle_profile(profile_path)

    cli_main(app_config, profile)


if __name__ == "__main__":
    main()
