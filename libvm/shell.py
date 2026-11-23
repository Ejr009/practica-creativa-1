"""Ejecución de comandos del sistema y error común del escenario."""

import logging
from pathlib import Path
import subprocess


log = logging.getLogger("auto-p2")
WORKDIR = Path.cwd()


class ErrorEscenario(RuntimeError):
    """Error de configuración o ejecución del escenario."""


def ejecutar(argumentos, *, cwd=None, comprobar=True):
    """Ejecuta un comando sin shell, registrando su ejecución."""
    args = [str(arg) for arg in argumentos]
    log.debug("Ejecutando: %s", " ".join(args))
    try:
        resultado = subprocess.run(
            args,
            cwd=str(cwd) if cwd else None,
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ErrorEscenario(f"No se encuentra el comando: {args[0]}") from exc

    if resultado.stdout.strip():
        log.debug("stdout: %s", resultado.stdout.strip())
    if resultado.stderr.strip():
        log.debug("stderr: %s", resultado.stderr.strip())
    if comprobar and resultado.returncode != 0:
        mensaje = resultado.stderr.strip() or resultado.stdout.strip()
        raise ErrorEscenario(f"Error ejecutando {' '.join(args)}: {mensaje}")
    return resultado
