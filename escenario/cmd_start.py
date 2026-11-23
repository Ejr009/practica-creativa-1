"""Orden start: arranca las VMs (los routers primero) y abre sus consolas."""

import logging

from escenario.bridges import ensure_bridges
from escenario.host_net import host_network
from escenario.state import load_state, select_vms
from lib_vm import VM


LOG = logging.getLogger("auto-p2")


def start_order(state):
    """FW, LB y C1 primero; después los servidores."""
    order = [n for n in ("fw", "lb", "c1") if n in state["vms"]]
    return order + [n for n in state["vms"] if n.startswith("s")]


def start(only=None):
    state = load_state()
    wanted = select_vms(state, only)
    ensure_bridges(state)
    host_network(state)
    # El script no espera a que cloud-init termine en cada VM.
    order = [name for name in start_order(state) if name in wanted]
    for name in order:
        VM(name).start_vm()
    for name in order:
        VM(name).show_console_vm()
    LOG.info("VMs arrancadas; espera a que cloud-init termine en cada una")
