# Guía: instalar y probar la práctica paso a paso

Se hace en un ordenador del laboratorio (UDS) con entorno gráfico. Cada paso tiene el comando, **qué hace** y **qué debes ver**. Copia **un comando por línea**.

**Qué es:** `auto-p2.py` crea, arranca, para y borra con un solo comando un escenario de 8 máquinas virtuales (cliente, cortafuegos, balanceador y hasta 5 servidores web).

```
C1 ──RED1── FW ──RED2── LB ──RED3── S1 … S5
```

Login de las VMs (si entras en alguna): usuario `root`, contraseña `cdps`.

---

## 0. Antes de empezar (una vez por terminal)

Algunos terminales marcan lo que pegas con `^[[200~` al principio y una `~` al final, y eso rompe los comandos. Desactívalo:

```bash
bind 'set enable-bracketed-paste off'
```

## 1. Preparar

```bash
/lab/cnvr/bin/prepare-vnx-debian
mkdir -p ~/pc1
cd ~/pc1
git clone https://github.com/Ejr009/practica-creativa-1.git
cd practica-creativa-1
cp /lab/cdps/pc1/cdps-vm-base-pc1.qcow2 .
ls
```

| Comando | Para qué |
| --- | --- |
| `prepare-vnx-debian` | Prepara KVM y Open vSwitch (solo hace falta una vez) |
| `git clone` | Baja el código en la carpeta `practica-creativa-1` |
| `cd practica-creativa-1` | Entra en ella: **todo se ejecuta desde aquí** |
| `cp ... .` | Copia la imagen base del sistema operativo (no está en Git) |

**Debe verse en el `ls`:** `auto-p2.py lib_vm.py libvm escenario auto-p2.json plantilla-vm-pc1.xml cdps-vm-base-pc1.qcow2`

## 2. Elegir el número de servidores (1 a 5)

```bash
cat auto-p2.json
```

Para cambiarlo sin editor: `sed -i 's/"num_servers": [0-9]*/"num_servers": 3/' auto-p2.json` (pon el número que quieras). Con `"debug": true` el script muestra cada comando que ejecuta.

## 3. `define`: crear el escenario (sin arrancarlo)

Estado antes (vacío):

```bash
sudo virsh list --all
sudo ovs-vsctl list-br
```

Crear:

```bash
python3 auto-p2.py define
```

Comprobar lo creado:

```bash
sudo virsh list --all
sudo ovs-vsctl list-br
ip -4 addr show RED1
ls
cat .cloud-init/s1/network-config
qemu-img info s1.qcow2
cat .auto-p2-state.json
```

**Qué debes ver:** las VMs en estado apagado; los bridges RED1, RED2 y RED3; la IP `10.0.10.3/26` del host en RED1; por cada VM un `.qcow2`, un `.xml` y una `.iso`; en `s1.qcow2` un `backing file` (disco diferencial: solo guarda lo que cambia sobre la imagen base); y en el estado, lo que creó el script para poder borrarlo después.

## 4. `start`: arrancar

```bash
python3 auto-p2.py start
```

Arranca fw, lb, c1 y los servidores, y abre una consola por VM. Al primer arranque, cada VM se configura sola con cloud-init (red, Apache en los servidores, HAProxy en lb). **Espera 1-2 minutos**, hasta ver `Reached target cloud-init.target` en las consolas.

## 5. Comprobar que funciona

```bash
python3 auto-p2.py monitor
```
Debe poner `ok` en todas. Si ves `sin respuesta`, espera y repite.

```bash
for i in 1 2 3 4 5 6; do curl -s http://10.0.10.130/; done
```
**Balanceo:** debe alternar `Servidor s1`, `s2`, `s3`... (HAProxy reparte en turnos, `roundrobin`).

```bash
curl -s "http://10.0.10.130:8404/stats;csv" | cut -d, -f1,2,18 | grep -E "^servers"
```
**Gestión de HAProxy:** muestra cada servidor `UP` o `DOWN`. También en el navegador: `http://10.0.10.130:8404/stats`.

**Comunicación entre redes** (el host está en RED1 y llega a las otras por FW):

```bash
ping -c 2 10.0.10.1
ping -c 2 10.0.10.130
ping -c 2 10.0.10.66
```

Desde dentro (consola de c1, login `root` / `cdps`): `ping -c 2 10.0.10.130` y `curl http://10.0.10.130`.

## 6. Parar y arrancar una sola VM

```bash
python3 auto-p2.py stop s1
python3 auto-p2.py monitor
for i in 1 2 3 4; do curl -s http://10.0.10.130/; done
python3 auto-p2.py start s1
```

Con `s1` apagada, `monitor` la muestra `shut off` y el balanceador sigue sirviendo con los demás. Tras `start s1` (espera 1 minuto), vuelve a aparecer.

## 7. Parar todo y comprobar la persistencia

En la consola de s1 (login `root` / `cdps`) crea un fichero:

```bash
echo prueba > /root/persiste.txt
```

Después, desde el host:

```bash
python3 auto-p2.py stop
python3 auto-p2.py monitor
python3 auto-p2.py start
```

Con `stop` todas pasan a `shut off` sin borrar discos. Tras `start` y 1-2 minutos, en s1: `cat /root/persiste.txt` debe seguir mostrando `prueba`, y `curl` al balanceador debe funcionar de nuevo.

## 8. Probar otro número de servidores

```bash
python3 auto-p2.py undefine
sed -i 's/"num_servers": [0-9]*/"num_servers": 2/' auto-p2.json
cat auto-p2.json
python3 auto-p2.py define
python3 auto-p2.py start
```

El `sed` cambia el número de servidores a 2 (pon el que quieras de 1 a 5) y el `cat` te deja comprobarlo. Si `nano` te abre el fichero vacío es que no estás en la carpeta `practica-creativa-1` (comprueba con `pwd`), y para recuperarlo: `git checkout auto-p2.json`. Tras 1-2 minutos, `monitor` debe mostrar solo s1 y s2, y los `curl` solo alternan entre ellos.

## 9. `undefine`: borrarlo todo

```bash
python3 auto-p2.py undefine
sudo virsh list --all
sudo ovs-vsctl list-br
ls
```

Apaga las VMs, las libera, quita la IP y las rutas del host y borra los bridges, los discos y el estado. **Debe quedar:** sin VMs ni bridges, y solo los scripts, la plantilla y la imagen base.

## 10. Pruebas automáticas (opcional)

No arrancan VMs ni tocan la red:

```bash
python3 -m unittest discover -s tests -v
```

## 11. Si algo falla

| Síntoma | Qué hacer |
| --- | --- |
| `can't open file '.../auto-p2.py'` | No estás dentro de `practica-creativa-1`: `cd ~/pc1/practica-creativa-1`. |
| `bash: $'\E[200~': orden no encontrada`, o `cd: ...pc1~: No existe` | Pegado con marcadores: ejecuta el apartado 0 y pega un comando por línea. |
| `Ya existe el escenario` | `python3 auto-p2.py undefine` y repite `define`. |
| `Faltan la imagen base o la plantilla XML` | Copia `cdps-vm-base-pc1.qcow2` y `plantilla-vm-pc1.xml` a la carpeta de trabajo. |
| `num_servers debe ser un entero de 1 a 5` | Corrige `auto-p2.json`. |
| `No hay terminal gráfico` | Usa una sesión con entorno gráfico o instala `xterm`. |
| `monitor` da `sin respuesta` o `curl` falla | cloud-init no ha terminado: espera 1-2 minutos y repite. |
| `sudo` pide contraseña | El script no es interactivo: hace falta `sudo` sin contraseña. |
| Escenario a medias o no sabes en qué estado está | `python3 auto-p2.py undefine` y vuelve a empezar. |

Útil: `sudo virsh list --all` (qué VMs existen) y `sudo virsh console s1` (consola de una VM; salir con Ctrl + ]).

## 12. Dónde está cada cosa en el código

| Orden | Qué hace | Dónde |
| --- | --- | --- |
| `define` | Bridges, red del host y, por VM: qcow2 diferencial, cloud-init, ISO, XML y `virsh define` | `escenario/cmd_define.py`; `libvm/net.py`, `libvm/cloud_init.py`, `libvm/xml_vm.py` y `VM.define_vm()` en `lib_vm.py` |
| `start [vm]` | `virsh start` y consola de cada VM | `escenario/cmd_start.py`; `VM.start_vm()`; `libvm/console.py` |
| `stop [vm]` | `virsh shutdown` y espera al apagado | `escenario/cmd_stop.py`; `VM.stop_vm()` |
| `monitor` | `virsh domstate` y `ping` desde el host | `escenario/cmd_monitor.py` |
| `undefine` | Apaga, `virsh undefine`, borra ficheros, rutas, IP del host y bridges | `escenario/cmd_undefine.py`; `escenario/host_net.py` |

La topología y las rutas salen de `escenario/topology.py`; Apache en los servidores y HAProxy en LB, de `escenario/services.py`. Todos los `.py` tienen 100 líneas o menos.
