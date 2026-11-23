"""Librería pública de la práctica: máquinas virtuales (VM) y redes (NET/Red)."""

import logging
from pathlib import Path
import shutil

from libvm import virsh
from libvm.cloud_init import write_cloud_init
from libvm.console import open_console
from libvm.net import NET, Red
from libvm.shell import ErrorEscenario, WORKDIR, ejecutar
from libvm.xml_vm import write_xml


__all__ = ["VM", "NET", "Red", "ErrorEscenario", "ejecutar"]
log = logging.getLogger("auto-p2")
TEMPLATE = WORKDIR / "plantilla-vm-pc1.xml"


class VM:
    """Una máquina virtual persistente gestionada por libvirt."""

    def __init__(self, name):
        self.name = name
        self.xml = WORKDIR / f"{name}.xml"
        self.disk = WORKDIR / f"{name}.qcow2"
        self.iso = WORKDIR / f"{name}-cdata.iso"
        self.cloud_dir = WORKDIR / ".cloud-init" / name

    def is_defined(self):
        return virsh.is_defined(self.name)

    def state(self):
        return virsh.domain_state(self.name)

    def define_vm(self, image, interfaces, forwarding=False, files=(), commands=()):
        """Crea disco COW, cloud-init y XML, y define la VM con virsh."""
        self._check_free(interfaces)
        ejecutar(["qemu-img", "create", "-F", "qcow2", "-f", "qcow2",
                  "-b", Path(image).resolve(), self.disk])
        write_cloud_init(self, interfaces, forwarding, files, commands)
        write_xml(self, interfaces, TEMPLATE)
        ejecutar(["sudo", "virsh", "define", self.xml])
        log.info("VM definida: %s", self.name)

    def _check_free(self, interfaces):
        if self.is_defined():
            raise ErrorEscenario(f"La VM {self.name} ya está definida en libvirt")
        for path in (self.disk, self.iso, self.xml):
            if path.exists():
                raise ErrorEscenario(f"El fichero ya existe: {path}")
        if not interfaces:
            raise ErrorEscenario(f"La VM {self.name} necesita al menos una interfaz")
        if not TEMPLATE.is_file():
            raise ErrorEscenario(f"Falta plantilla XML: {TEMPLATE}")

    def start_vm(self):
        if not self.is_defined():
            raise ErrorEscenario(f"VM no definida: {self.name}")
        if self.state() == "running":
            log.info("VM ya arrancada: %s", self.name)
            return
        ejecutar(["sudo", "virsh", "start", self.name])
        log.info("VM arrancada: %s", self.name)

    def show_console_vm(self):
        open_console(self.name)

    def stop_vm(self):
        estado = self.state()
        if estado is None or estado == "shut off":
            log.info("VM ya apagada o no definida: %s", self.name)
        elif estado == "running":
            ejecutar(["sudo", "virsh", "shutdown", self.name])
            log.info("Solicitado apagado ordenado de %s", self.name)
        else:
            log.info("Estado de %s: %s", self.name, estado)

    def undefine_vm(self):
        if not self.is_defined():
            return
        if self.state() != "shut off":
            raise ErrorEscenario(f"No se libera {self.name}: primero debe estar apagada")
        ejecutar(["sudo", "virsh", "undefine", self.name])
        log.info("VM liberada: %s", self.name)

    def remove_files(self):
        for path in (self.disk, self.xml, self.iso):
            if path.exists():
                path.unlink()
                log.debug("Eliminado: %s", path)
        if self.cloud_dir.exists():
            shutil.rmtree(self.cloud_dir)
