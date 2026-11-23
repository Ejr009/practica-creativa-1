"""Orden define: crea redes, red del host y las VMs (apagadas) del escenario."""

import logging

from escenario.bridges import ensure_bridges
from escenario.cmd_undefine import undefine
from escenario.host_net import host_network
from escenario.services import services
from escenario.settings import BASE, STATE, TEMPLATE
from escenario.state import save_state
from escenario.topology import specifications
from libvm.shell import ErrorEscenario
from lib_vm import VM


LOG = logging.getLogger("auto-p2")


def check_free(specs):
    """Ninguna VM ni fichero con esos nombres puede existir ya."""
    for name, _, _ in specs:
        vm = VM(name)
        if vm.is_defined():
            raise ErrorEscenario(f"Ya existe la VM {name} en libvirt (¿prueba manual?)")
        for path in (vm.xml, vm.disk, vm.iso):
            if path.exists():
                raise ErrorEscenario(f"Existe un fichero que usaría el script: {path}")


def rollback(error):
    """Deshace lo creado a medias; si no puede, conserva el estado."""
    LOG.error("Fallo durante define; intentando deshacer los cambios parciales")
    try:
        undefine()
    except (ErrorEscenario, OSError) as cleanup_error:
        raise ErrorEscenario(
            f"Falló define ({error}) y la limpieza parcial ({cleanup_error}). "
            "Conservamos el estado para reintentar 'undefine'."
        ) from error


def define(num_servers):
    if STATE.exists():
        raise ErrorEscenario("Ya existe el escenario; usa 'undefine' antes de redefinirlo")
    if not BASE.is_file() or not TEMPLATE.is_file():
        raise ErrorEscenario("Faltan la imagen base o la plantilla XML de PC1")
    specs = specifications(num_servers)
    check_free(specs)
    state = {"created_by": "auto-p2.py", "vms": [n for n, _, _ in specs],
             "bridges_added": [], "host_address_added": False, "host_routes_added": []}
    save_state(state)
    LOG.info("Definiendo escenario con %s servidores", num_servers)
    try:
        ensure_bridges(state)
        host_network(state)
        for name, interfaces, forwarding in specs:
            VM(name).define_vm(BASE, interfaces, forwarding=forwarding,
                               **services(name, num_servers))
    except (ErrorEscenario, OSError) as exc:
        rollback(exc)
        raise
    LOG.info("Escenario definido. Ahora ejecuta 'python3 auto-p2.py start'")
