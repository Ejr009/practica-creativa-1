"""Orden monitor: estado de cada VM y ping desde el host."""

from escenario.state import load_state
from escenario.topology import specifications
from libvm.shell import ejecutar
from lib_vm import VM


def monitor():
    """Muestra el estado de cada VM y si responde a ping desde el host."""
    state = load_state()
    print(f"{'VM':<5}{'ESTADO':<12}{'IP':<14}PING")
    for name, interfaces, _ in specifications(len(state["vms"]) - 3):
        ip = interfaces[0]["addr"].split("/")[0]
        estado = VM(name).state() or "no definida"
        ping = "-"
        if estado == "running":
            ok = ejecutar(["ping", "-c", "1", "-W", "1", ip], comprobar=False).returncode == 0
            ping = "ok" if ok else "sin respuesta"
        print(f"{name:<5}{estado:<12}{ip:<14}{ping}")
