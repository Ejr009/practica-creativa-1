"""Orden undefine: libera todo lo que creó el escenario."""

import logging

from escenario.cmd_stop import shutdown_all
from escenario.host_net import release_host
from escenario.settings import ROOT, STATE
from escenario.state import load_state
from libvm.net import NET
from lib_vm import VM


LOG = logging.getLogger("auto-p2")


def remove_vms(state):
    """Libera las VMs en orden inverso y borra sus ficheros."""
    for name in reversed(state["vms"]):
        VM(name).undefine_vm()
    for name in state["vms"]:
        VM(name).remove_files()
    cloud_root = ROOT / ".cloud-init"
    if cloud_root.exists() and not any(cloud_root.iterdir()):
        cloud_root.rmdir()


def undefine():
    state = load_state()
    LOG.info("Liberando escenario (con apagado ordenado previo)")
    shutdown_all(state["vms"])
    remove_vms(state)
    release_host(state)
    for name in reversed(state["bridges_added"]):
        NET(name).destroy_net()
    STATE.unlink()
    STATE.with_name(STATE.name + ".tmp").unlink(missing_ok=True)
    LOG.info("Escenario liberado; se conservan la imagen base, XML plantilla y scripts")
