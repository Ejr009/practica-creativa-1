# CDPS — Práctica Creativa 1 (2026–27)

Automatización en Python del escenario de balanceador de la Práctica 2 de CDPS (ETSIT-UPM) usando KVM/libvirt, Open vSwitch y cloud-init.

## Estado

**Implementación obligatoria validada.** Probada en el laboratorio remoto con 1, 3 y 5 servidores, incluyendo conectividad IP, apagado, reinicio, persistencia y limpieza. Superadas 16 pruebas automáticas, incluidas pruebas de manejo de errores y rollback. Las funcionalidades adicionales quedan pendientes.

## Estructura

- `auto-p2.py`: programa principal y órdenes `define`, `start`, `stop` y `undefine`.
- `lib_vm.py`: gestión de máquinas virtuales y redes.
- `auto-p2.json`: configuración de `num_servers` (entero de 1 a 5) y `debug`.
- `plantilla-vm-pc1.xml`: plantilla original para generar especificaciones de VMs.

La imagen base `cdps-vm-base-pc1.qcow2` **no se versiona** (es grande y se obtiene del material oficial del laboratorio).

## Preparación en el laboratorio

1. Antes de las operaciones de virtualización, ejecutar `/lab/cnvr/bin/prepare-vnx-debian`.
2. Trabajar en un directorio propio que contenga estos cuatro archivos y la imagen base oficial `cdps-vm-base-pc1.qcow2` (disponible en `/lab/cdps/pc1/`).
3. Ajustar `auto-p2.json` al número de servidores deseado y ejecutar:

```bash
python3 auto-p2.py define
python3 auto-p2.py start
python3 auto-p2.py stop
python3 auto-p2.py undefine
```

`undefine` elimina discos diferenciales y configuraciones generadas; antes de ejecutarlo, conservar cualquier dato que se necesite en el entorno virtual.

## Pruebas offline

Sin arrancar VMs ni modificar la red del host, ejecutar desde la raíz:

```bash
python3 -m unittest discover -s tests -v
```

Las pruebas emplean mocks para comandos de KVM/OVS; antes de integrar cambios es necesario repetir las pruebas reales en el laboratorio.

## Colaboración

- `main`: versión funcional revisada.
- Ramas `fix/...` y `feature/...` para correcciones y mejoras.
- Integración mediante pull requests tras comprobar que no hay regresiones.

## Entrega académica

El entregable oficial es el código empaquetado en ZIP/TGZ a Moodle y una defensa oral, no este repositorio por sí solo. Cada integrante deberá comprender y poder explicar el código. El repositorio puede compartirse con el equipo mediante permisos de colaboración cuando se acuerde. Evitar incorporar imágenes de VM, archivos temporales o credenciales.
