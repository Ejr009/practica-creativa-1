"""Consultas a libvirt: si una VM existe y en qué estado está."""

from libvm.shell import ErrorEscenario, ejecutar


# libvirt puede devolver el estado en español o en inglés.
ALIAS = {
    "ejecutando": "running",
    "en ejecución": "running",
    "apagado": "shut off",
    "apagada": "shut off",
    "pausado": "paused",
    "en pausa": "paused",
}


def is_defined(name):
    """Comprueba si la VM existe, notificando errores de libvirt."""
    resultado = ejecutar(["sudo", "virsh", "list", "--all", "--name"])
    return name in (line.strip() for line in resultado.stdout.splitlines())


def domain_state(name):
    """Estado normalizado de la VM, o None si no está definida."""
    resultado = ejecutar(["sudo", "virsh", "domstate", name], comprobar=False)
    if resultado.returncode != 0:
        if is_defined(name):
            detalle = resultado.stderr.strip() or resultado.stdout.strip()
            raise ErrorEscenario(
                f"No se pudo consultar el estado de {name}: {detalle}"
            )
        return None
    estado = resultado.stdout.strip().lower()
    return ALIAS.get(estado, estado)
