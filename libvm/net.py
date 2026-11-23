"""Redes virtuales: un bridge Open vSwitch por red (RED1, RED2 y RED3)."""

import logging

from libvm.shell import ErrorEscenario, ejecutar


log = logging.getLogger("auto-p2")


class NET:
    """Un bridge Open vSwitch."""

    def __init__(self, name):
        self.name = name

    def exists(self):
        resultado = ejecutar(
            ["sudo", "ovs-vsctl", "br-exists", self.name], comprobar=False
        )
        if resultado.returncode == 0:
            return True
        if resultado.returncode == 2:
            return False
        detalle = resultado.stderr.strip() or resultado.stdout.strip()
        raise ErrorEscenario(
            f"No se pudo consultar el bridge {self.name}: {detalle}"
        )

    def create_net(self):
        """Crea el bridge y devuelve True si era nuevo."""
        if self.exists():
            log.info("El bridge %s ya existía; se reutiliza", self.name)
            return False
        ejecutar(["sudo", "ovs-vsctl", "add-br", self.name])
        log.info("Bridge creado: %s", self.name)
        return True

    def destroy_net(self):
        if self.exists():
            ejecutar(["sudo", "ovs-vsctl", "del-br", self.name])
            log.info("Bridge eliminado: %s", self.name)


# El enunciado habla de una clase Red; el esqueleto oficial la llama NET.
Red = NET
