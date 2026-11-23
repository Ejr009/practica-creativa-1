# CDPS — Práctica Creativa 1 (2026–27)

Automatización en Python del escenario de la Práctica 2 mediante KVM/libvirt, Open vSwitch y cloud-init. Implementa las órdenes obligatorias `define`, `start`, `stop` y `undefine`, con 1 a 5 servidores.

## Estado

Implementación obligatoria RQ1–RQ10 completada. Probada en UDS con todas las configuraciones de 1 a 5 servidores (despliegue, conectividad IP, apagado, reinicio, persistencia y limpieza), además de 25 pruebas automáticas. Opcionales implementados: `monitor`, Apache + HAProxy automáticos, interfaz de gestión de HAProxy y `start`/`stop` por VM (las nuevas aún sin validar en UDS). Pendiente: filtrado en FW (ufw).

## Topología y direccionamiento

```text
 ┌───────┐  ┌───────┐
 │   C1  │  │  Host │
 └───┬───┘  └───┬───┘
     │.2        │.3
═════╧══════════╧═════════╤══════  RED1  10.0.10.0/26
                          │.1
                   ┌──────┴──────┐
                   │      FW     │
                   │  ip_forward │
                   └──────┬──────┘
                          │.129
                      ════╧═════════════╤════  RED2  10.0.10.128/26
                                        │.130
                                ┌───────┴──────┐
                                │      LB      │
                                │ HAProxy :80  │
                                └───────┬──────┘
                                        │.65
            RED3  10.0.10.64/26
            ════╤═══════════╤═══════════╪═══════════╤═══════════╤════
                │.66        │.67        │.68        │.69        │.70
            ┌───┴───┐   ┌───┴───┐   ┌───┴───┐   ┌───┴───┐   ┌───┴───┐
            │   S1  │   │   S2  │   │   S3  │   │   S4  │   │   S5  │
            └───────┘   └───────┘   └───────┘   └───────┘   └───────┘
```

S1–S5 existen según `num_servers` (1 a 5). Todas las interfaces usan prefijo `/26` dentro del bloque `10.0.10.0/24`.

| Red | Subred | Dispositivos |
| --- | --- | --- |
| RED1 | `10.0.10.0/26` | C1 `.2`, Host `.3`, FW `.1` |
| RED2 | `10.0.10.128/26` | FW `.129`, LB `.130` |
| RED3 | `10.0.10.64/26` | LB `.65`, S1–S5 `.66`–`.70` |

| Sistema | Interfaces | Rutas | Reenvío IP |
| --- | --- | --- | --- |
| C1 | eth0 RED1 `.2` | por defecto vía `10.0.10.1` (FW) | no |
| FW | eth0 RED1 `.1`, eth1 RED2 `.129` | `10.0.10.64/26` vía `10.0.10.130` (LB) | sí |
| LB | eth0 RED2 `.130`, eth1 RED3 `.65` | por defecto vía `10.0.10.129` (FW) | sí |
| S1–S5 | eth0 RED3 `.66`–`.70` | por defecto vía `10.0.10.65` (LB) | no |
| Host | bridge RED1 `.3` | `10.0.10.128/26` y `10.0.10.64/26` vía `10.0.10.1` (FW) | — |

Cada sistema sale por su vecino: C1 y el host usan FW, FW llega a RED3 a través de LB, LB vuelve a RED1 a través de FW y los servidores usan LB. El filtrado en FW (ufw) no está implementado.

## Archivos

| Archivo | Función |
| --- | --- |
| `auto-p2.py` | Punto de entrada: lee los argumentos y llama a la orden |
| `lib_vm.py` | Librería pública: clases `VM` y `NET` (también `Red`) |
| `libvm/` | Piezas de la librería: `shell`, `net`, `virsh`, `cloud_init`, `xml_vm`, `console` |
| `escenario/` | Lógica del escenario: `topology`, `services`, `state`, `host_net`, `bridges` y una orden por fichero (`cmd_*.py`) |
| `auto-p2.json` | Número de servidores y nivel de depuración |
| `plantilla-vm-pc1.xml` | Plantilla XML oficial para las VMs |
| `tests/` | Pruebas automáticas sin levantar máquinas virtuales (cada script ≤ 100 líneas) |

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
| `start <vm>` / `stop <vm>` | Igual que `start`/`stop` pero solo para una VM (p. ej. `start s1`) |
| `monitor` | Muestra estado de cada VM y ping desde el host; usar con `watch -n2 python3 auto-p2.py monitor` |
| `undefine` | Apaga, libera las VMs y elimina los recursos generados por el escenario |

La configuración se aplica con cloud-init: `meta-data` identifica cada VM, `network-config` establece sus interfaces y rutas y `user-data` configura el hostname, el reenvío IP en FW/LB y la reaplicación de Netplan tras reinicios. Las tres entradas se empaquetan en una ISO NoCloud para cada VM.

El inventario del escenario se guarda en `.auto-p2-state.json` para que la limpieza no dependa de cambios posteriores en `auto-p2.json`. `undefine` elimina los discos y configuraciones generados, pero conserva la imagen base y la plantilla. **Guardar antes cualquier dato que se quiera conservar de las VMs.**

## Balanceador y servidores web

Por cloud-init, cada `sN` arranca Apache con una página que muestra su nombre y LB arranca HAProxy (`roundrobin` entre los servidores definidos). Tras unos segundos de cloud-init:

```bash
curl http://10.0.10.130/        # repetir: alterna s1, s2, ...
# gestión web de HAProxy: http://10.0.10.130:8404/stats (permite activar/desactivar servidores)
# API en tiempo de ejecución, dentro de LB (requiere socat):
echo "show servers state" | sudo socat stdio /run/haproxy/admin.sock
```

## Validación

Las pruebas unitarias no arrancan VMs ni modifican redes del host:

```bash
python3 -m unittest discover -s tests -v
```

Para las pruebas reales en UDS, comprobar `sudo virsh list --all`, `cloud-init status`, conectividad IP entre las VMs, persistencia después de `stop`/`start` y ausencia de recursos generados después de `undefine`. Las pruebas unitarias emplean mocks, por lo que no sustituyen la validación real en el laboratorio.

## Colaboración y entrega

La rama `main` mantiene la versión revisada; las mejoras se integran mediante ramas y pull requests. La entrega oficial consiste en el código empaquetado en un ZIP/TGZ en Moodle y una defensa oral. Todos los integrantes deben comprender y poder explicar el código; no se deben incluir imágenes de VM, archivos temporales ni credenciales.
