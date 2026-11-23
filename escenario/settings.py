"""Rutas y constantes del escenario (se calculan desde el directorio de trabajo)."""

from pathlib import Path


ROOT = Path.cwd()
CONFIG = ROOT / "auto-p2.json"
STATE = ROOT / ".auto-p2-state.json"
BASE = ROOT / "cdps-vm-base-pc1.qcow2"
TEMPLATE = ROOT / "plantilla-vm-pc1.xml"
NETWORKS = ("RED1", "RED2", "RED3")
HOST_ROUTES = ("10.0.10.128/26", "10.0.10.64/26")
HOST_ADDRESS = "10.0.10.3/26"
HOST_GATEWAY = "10.0.10.1"
