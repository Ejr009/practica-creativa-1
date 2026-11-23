"""Red del host: dirección .3 en RED1 y rutas hacia RED2 y RED3 a través de FW."""

import logging

from escenario.settings import HOST_ADDRESS, HOST_GATEWAY, HOST_ROUTES
from escenario.state import save_state
from libvm.shell import ErrorEscenario, ejecutar


LOG = logging.getLogger("auto-p2")


def host_network(state):
    """Configura RED1 en el host. Cada recurso se anota antes de crearlo."""
    ejecutar(["sudo", "ip", "link", "set", "dev", "RED1", "up"])
    addresses = ejecutar(["ip", "-4", "-o", "addr", "show", "dev", "RED1"]).stdout
    if HOST_ADDRESS not in addresses:
        state["host_address_added"] = True
        save_state(state)
        ejecutar(["sudo", "ip", "addr", "add", HOST_ADDRESS, "dev", "RED1"])
    for network in HOST_ROUTES:
        existing = ejecutar(["ip", "-4", "route", "show", network]).stdout.strip()
        if not existing:
            if network not in state["host_routes_added"]:
                state["host_routes_added"].append(network)
                save_state(state)
            ejecutar(["sudo", "ip", "route", "add", network,
                      "via", HOST_GATEWAY, "dev", "RED1"])
        elif f"via {HOST_GATEWAY}" not in existing or "dev RED1" not in existing:
            raise ErrorEscenario(f"Existe una ruta conflictiva hacia {network}: {existing}")
    LOG.info("Host configurado en RED1 (%s)", HOST_ADDRESS)


def _detail(result):
    return result.stderr.strip() or result.stdout.strip()


def _remove_route(network):
    result = ejecutar(["sudo", "ip", "route", "del", network,
                       "via", HOST_GATEWAY, "dev", "RED1"], comprobar=False)
    if result.returncode == 0:
        return
    if ejecutar(["ip", "-4", "route", "show", network]).stdout.strip():
        raise ErrorEscenario(f"No se pudo eliminar la ruta {network}: {_detail(result)}")
    LOG.warning("Ruta ya ausente: %s", network)


def _remove_address():
    result = ejecutar(["sudo", "ip", "addr", "del", HOST_ADDRESS, "dev", "RED1"],
                      comprobar=False)
    if result.returncode == 0:
        return
    lines = ejecutar(["ip", "-4", "-o", "addr", "show"]).stdout.splitlines()
    if any(line.split()[1].split("@")[0] == "RED1" and f"inet {HOST_ADDRESS}" in line
           for line in lines):
        raise ErrorEscenario(
            f"No se pudo eliminar la dirección {HOST_ADDRESS}: {_detail(result)}")
    LOG.warning("Dirección del host ya ausente: %s", HOST_ADDRESS)


def release_host(state):
    """Quita solo las rutas y la dirección que añadió este escenario."""
    for network in state["host_routes_added"]:
        _remove_route(network)
    if state["host_address_added"]:
        _remove_address()
