"""Journal des actions de diagnostic (traçabilité — utile en atelier).

Contrairement à un simple historique de scripts lancés, chaque ligne décrit
une action réelle effectuée sur le véhicule (lecture/effacement de codes
défauts, test actionneur, écriture de paramètre)."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Union

DEFAULT_HISTORY_PATH = "config/historique.log"


def log_event(message: str, path: Union[str, Path] = DEFAULT_HISTORY_PATH) -> None:
    horodatage = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{horodatage} - {message}\n")


def read_recent(n: int = 20, path: Union[str, Path] = DEFAULT_HISTORY_PATH) -> List[str]:
    file_path = Path(path)
    if not file_path.exists():
        return []
    lignes = file_path.read_text(encoding="utf-8").splitlines()
    return lignes[-n:]
