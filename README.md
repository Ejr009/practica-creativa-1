# CDPS — Práctica Creativa 1 (2026–27)

Automatización en Python del escenario de la Práctica 2 mediante KVM/libvirt, Open vSwitch y cloud-init. Implementa las órdenes obligatorias `define`, `start`, `stop` y `undefine`, con 1 a 5 servidores.

## Estado

Implementación obligatoria RQ1–RQ10 completada. Probada en UDS con todas las configuraciones de 1 a 5 servidores (despliegue, conectividad IP, apagado, reinicio, persistencia y limpieza), además de 21 pruebas automáticas. Las funcionalidades opcionales están pendientes.

## Topología y direccionamiento

```text
  Host (.3)      C1 (.2)
     |             |
     +---- RED1 ---+---- FW (.1 / .129)
                            |
                           RED2
                            |
                        LB (.130 / .65)
                            |
                           RED3
                       +----+----+
                       S1   ...  S5
                      (.66)     (.70)
```

| Red | Subred | Interfaces |
| --- | --- | --- |
| RED1 | `10.0.10.0/26` | C1 `.2`, FW `.1`, host `.3` |
| RED2 | `10.0.10.128/26` | FW `.129`, LB `.130` |
| RED3 | `10.0.10.64/26` | LB `.65`, S1–S5 `.66`–`.70` |

Todas las direcciones indicadas pertenecen al bloque `10.0.10.0/24` y las interfaces tienen prefijo `/26`. Se crean únicamente los servidores indicados en `auto-p2.json`.

El encaminamiento es estático: C1 utiliza FW como puerta de enlace; FW llega a RED3 a través de LB; LB vuelve a RED1 mediante FW; y los servidores utilizan LB como puerta de enlace. El host tiene una dirección en RED1 y rutas hacia RED2 y RED3 a través de FW. El filtrado en FW y el balanceo HTTP en LB pertenecen a las partes opcionales, aún no implementadas.

## Archivos

| Archivo | Función |
| --- | --- |
| `auto-p2.py` | Programa principal, topología y ciclo de vida del escenario |
| `lib_vm.py` | Clases `VM` y `NET` (también exportada como `Red`) |
| `auto-p2.json` | Número de servidores y nivel de depuración |
| `plantilla-vm-pc1.xml` | Plantilla XML oficial para las VMs |
| `tests/` | Pruebas automáticas sin levantar máquinas virtuales |

La imagen base `cdps-vm-base-pc1.qcow2` se obtiene del laboratorio (`/lab/cdps/pc1/`) y **no se incluye en Git**. El script tampoco la copia: debe estar ya en el directorio de trabajo, junto a la plantilla y los scripts.

## Ejecución en UDS

1. Preparar el servidor con `/lab/cnvr/bin/prepare-vnx-debian`.
2. Trabajar en un directorio propio con los archivos anteriores y la imagen base.
3. Configurar `auto-p2.json` (valores permitidos: `num_servers` de 1 a 5 y `debug` booleano).
4. Ejecutar, en este orden:

```bash
python3 auto-p2.py define
python3 auto-p2.py start
python3 auto-p2.py stop
python3 auto-p2.py undefine
```

| Orden | Qué hace |
| --- | --- |
| `define` | Crea bridges OVS, red del host, discos QCOW2 diferenciales, ISOs cloud-init, XML y definiciones libvirt |
| `start` | Arranca las VMs y abre sus consolas; hay que esperar a que cloud-init termine |
| `stop` | Solicita apagado ordenado, comprueba el estado y conserva los discos |
| `undefine` | Apaga, libera las VMs y elimina los recursos generados por el escenario |

La configuración se aplica con cloud-init: `meta-data` identifica cada VM, `network-config` establece sus interfaces y rutas y `user-data` configura el hostname, el reenvío IP en FW/LB y la reaplicación de Netplan tras reinicios. Las tres entradas se empaquetan en una ISO NoCloud para cada VM.

El inventario del escenario se guarda en `.auto-p2-state.json` para que la limpieza no dependa de cambios posteriores en `auto-p2.json`. `undefine` elimina los discos y configuraciones generados, pero conserva la imagen base y la plantilla. **Guardar antes cualquier dato que se quiera conservar de las VMs.**

## Validación

Las pruebas unitarias no arrancan VMs ni modifican redes del host:

```bash
python3 -m unittest discover -s tests -v
```

Para las pruebas reales en UDS, comprobar `sudo virsh list --all`, `cloud-init status`, conectividad IP entre las VMs, persistencia después de `stop`/`start` y ausencia de recursos generados después de `undefine`. Las pruebas unitarias emplean mocks, por lo que no sustituyen la validación real en el laboratorio.

## Colaboración y entrega

La rama `main` mantiene la versión revisada; las mejoras se integran mediante ramas y pull requests. La entrega oficial consiste en el código empaquetado en un ZIP/TGZ en Moodle y una defensa oral. Todos los integrantes deben comprender y poder explicar el código; no se deben incluir imágenes de VM, archivos temporales ni credenciales.
