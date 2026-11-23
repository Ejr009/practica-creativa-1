"""Orden stop: apagado ordenado de todas las VMs o de una sola."""

import logging
import time

from escenario.state import load_state, select_vms
from libvm.shell import ErrorEscenario
from lib_vm import VM


LOG = logging.getLogger("auto-p2")


def shutdown_all(names):
    """Pide el apagado de cada VM y espera hasta 90 s a que terminen."""
    for name in names:
        VM(name).stop_vm()
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        remaining = [n for n in names if VM(n).state() not in (None, "shut off")]
        if not remaining:
            return
        time.sleep(2)
    raise ErrorEscenario(
        "Las VMs no se han apagado dentro del plazo: " + ", ".join(remaining)
        + ". Comprueba 'sudo virsh list --all'; no se ha forzado su apagado."
    )


def stop(only=None):
    state = load_state()
    LOG.info("Solicitando apagado ordenado sin borrar discos")
    shutdown_all(select_vms(state, only))
    LOG.info("VMs paradas. Los datos permanecen en los QCOW2")
