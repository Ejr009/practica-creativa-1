"""Creación de los bridges RED1, RED2 y RED3 anotándolos en el estado."""

import logging

from escenario.settings import NETWORKS
from escenario.state import save_state
from libvm.net import NET


LOG = logging.getLogger("auto-p2")


def ensure_bridges(state):
    """Crea los bridges que falten. Se anota cada uno antes de crearlo,
    para que undefine solo borre los que ha creado este escenario."""
    for name in NETWORKS:
        net = NET(name)
        if net.exists():
            LOG.debug("El bridge %s ya existe; se reutiliza", name)
            continue
        tracked = name in state["bridges_added"]
        if not tracked:
            state["bridges_added"].append(name)
            save_state(state)
        if not net.create_net() and not tracked:
            state["bridges_added"].remove(name)
            save_state(state)
