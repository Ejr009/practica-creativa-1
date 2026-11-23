"""Estado guardado (.auto-p2-state.json): qué ha creado el script, para deshacerlo."""

import json

from escenario.settings import HOST_ROUTES, NETWORKS, STATE
from libvm.shell import ErrorEscenario


def save_state(state):
    """Escribe el estado de forma atómica para evitar archivos truncados."""
    temporary = STATE.with_name(STATE.name + ".tmp")
    try:
        temporary.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        temporary.replace(STATE)
    except OSError as exc:
        raise ErrorEscenario(f"No se puede guardar el estado: {exc}") from exc


def _unique_strings(values, allowed):
    return (isinstance(values, list) and len(values) == len(set(map(str, values)))
            and all(isinstance(x, str) and x in allowed for x in values))


def load_state():
    """Valida el inventario antes de operar sobre VMs y archivos locales."""
    if not STATE.is_file():
        raise ErrorEscenario("Escenario no definido por auto-p2.py; ejecuta 'define'")
    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise ErrorEscenario(f"No se puede leer el estado: {exc}") from exc
    if not isinstance(state, dict) or state.get("created_by") != "auto-p2.py":
        raise ErrorEscenario("Archivo de estado no reconocido")
    vms = state.get("vms")
    if not isinstance(vms, list) or not 4 <= len(vms) <= 8:
        raise ErrorEscenario("Inventario de VMs inválido en el archivo de estado")
    if vms != ["c1", "fw", "lb"] + [f"s{i}" for i in range(1, len(vms) - 2)]:
        raise ErrorEscenario("Nombres u orden de VMs inválidos en el archivo de estado")
    if not _unique_strings(state.get("bridges_added"), NETWORKS):
        raise ErrorEscenario("Bridges inválidos en el archivo de estado")
    if not _unique_strings(state.get("host_routes_added"), HOST_ROUTES):
        raise ErrorEscenario("Rutas inválidas en el archivo de estado")
    if type(state.get("host_address_added")) is not bool:
        raise ErrorEscenario("Dirección del host inválida en el archivo de estado")
    return state


def select_vms(state, only):
    """Devuelve las VMs a tratar: todas o solo la indicada."""
    if only is None:
        return list(state["vms"])
    if only not in state["vms"]:
        raise ErrorEscenario(f"VM desconocida: {only} (opciones: {', '.join(state['vms'])})")
    return [only]
