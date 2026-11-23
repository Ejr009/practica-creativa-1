"""Apertura de una consola gráfica para una VM sin bloquear el script."""

import logging
import shutil
import subprocess

from libvm.shell import ErrorEscenario


log = logging.getLogger("auto-p2")


def console_command(name):
    """Primer terminal disponible: gnome-terminal, xfce4-terminal, xterm o virt-viewer."""
    opciones = [
        ("gnome-terminal", ["gnome-terminal", "--title", name, "--",
                            "sudo", "virsh", "console", name]),
        ("xfce4-terminal", ["xfce4-terminal", "-T", name, "--hide-menubar",
                            "-e", f"sudo virsh console {name}"]),
        ("xterm", ["xterm", "-T", name, "-e", "sudo", "virsh", "console", name]),
        ("virt-viewer", ["virt-viewer", name]),
    ]
    for programa, comando in opciones:
        if shutil.which(programa):
            return comando
    raise ErrorEscenario("No hay terminal gráfico para abrir las consolas")


def open_console(name):
    comando = console_command(name)
    log.debug("Abriendo consola: %s", name)
    try:
        subprocess.Popen(comando, stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
    except OSError as exc:
        raise ErrorEscenario(f"No se puede abrir consola de {name}: {exc}") from exc
