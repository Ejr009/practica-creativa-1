"""Generación del XML de libvirt de una VM a partir de la plantilla."""

import copy
import xml.etree.ElementTree as ET

from libvm.shell import ErrorEscenario


def load_template(template):
    """Lee la plantilla y devuelve el árbol y sus elementos clave."""
    try:
        tree = ET.parse(template)
    except ET.ParseError as exc:
        raise ErrorEscenario(f"Plantilla XML inválida: {exc}") from exc
    root = tree.getroot()
    parts = {
        "name": root.find("name"),
        "disk": root.find("./devices/disk[@device='disk']/source"),
        "iso": root.find("./devices/disk[@device='cdrom']/source"),
        "devices": root.find("devices"),
        "iface": root.find("./devices/interface"),
    }
    if any(part is None for part in parts.values()):
        raise ErrorEscenario("La plantilla XML no tiene la estructura esperada")
    return tree, parts


def set_interfaces(devices, original, interfaces):
    """Sustituye la interfaz de la plantilla por una por cada red de la VM."""
    first_pos = list(devices).index(original)
    for old in devices.findall("interface"):
        devices.remove(old)
    for index, iface in enumerate(interfaces):
        new = copy.deepcopy(original)
        source = new.find("source")
        if source is None:
            raise ErrorEscenario("La interfaz de la plantilla no tiene <source>")
        source.set("bridge", iface["bridge"])
        mac = new.find("mac")  # sin MAC fija: libvirt asigna una distinta
        if mac is not None:
            new.remove(mac)
        devices.insert(first_pos + index, new)


def write_xml(vm, interfaces, template):
    """Escribe vm.xml con el nombre, el disco, la ISO y las interfaces de la VM."""
    tree, parts = load_template(template)
    parts["name"].text = vm.name
    parts["disk"].set("file", str(vm.disk))
    parts["iso"].set("file", str(vm.iso))
    set_interfaces(parts["devices"], parts["iface"], interfaces)
    ET.indent(tree, space="  ")
    tree.write(vm.xml, encoding="unicode", xml_declaration=True)
