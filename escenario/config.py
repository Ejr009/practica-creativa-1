"""Lectura de auto-p2.json y configuración de las trazas (logging)."""

import json
import logging
import sys

from escenario.settings import CONFIG
from libvm.shell import ErrorEscenario


def read_config():
    """Lee y valida num_servers (1 a 5) y debug (true o false)."""
    if not CONFIG.is_file():
        raise ErrorEscenario(f"Falta {CONFIG.name}")
    try:
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise ErrorEscenario(f"JSON no válido: {exc}") from exc
    if not isinstance(cfg, dict):
        raise ErrorEscenario("auto-p2.json debe contener un objeto JSON")
    count = cfg.get("num_servers")
    if type(count) is not int or not 1 <= count <= 5:
        raise ErrorEscenario("num_servers debe ser un entero de 1 a 5")
    if type(cfg.get("debug", False)) is not bool:
        raise ErrorEscenario("debug debe ser true o false")
    return cfg


def initialize_logging(debug):
    """INFO por defecto; DEBUG (cada comando ejecutado) si debug es true."""
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stdout,
    )
