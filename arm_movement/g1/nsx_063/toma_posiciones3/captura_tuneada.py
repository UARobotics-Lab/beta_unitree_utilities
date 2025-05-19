import sys
import time
import math
import json
from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelSubscriber
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_

class G1JointIndex:
    LeftHipPitch = 0
    LeftHipRoll = 1
    LeftHipYaw = 2
    LeftKnee = 3
    LeftAnklePitch = 4
    LeftAnkleRoll = 5
    RightHipPitch = 6
    RightHipRoll = 7
    RightHipYaw = 8
    RightKnee = 9
    RightAnklePitch = 10
    RightAnkleRoll = 11
    WaistYaw = 12
    WaistRoll = 13
    WaistPitch = 14
    LeftShoulderPitch = 15
    LeftShoulderRoll = 16
    LeftShoulderYaw = 17
    LeftElbow = 18
    LeftWristRoll = 19
    LeftWristPitch = 20
    LeftWristYaw = 21
    RightShoulderPitch = 22
    RightShoulderRoll = 23
    RightShoulderYaw = 24
    RightElbow = 25
    RightWristRoll = 26
    RightWristPitch = 27
    RightWristYaw = 28

BRAZO_IZQ = [15, 16, 17, 18, 19, 20, 21]
BRAZO_DER = [22, 23, 24, 25, 26, 27, 28]
CINTURA = [12, 13, 14]
BRAZOS_Y_CINTURA = BRAZO_IZQ + BRAZO_DER + CINTURA

MIRROR_MAP = {
    15: (22, 1),
    16: (23, -1),
    17: (24, -1),
    18: (25, 1),
    19: (26, -1),
    20: (27, 1),
    21: (28, -1)
}

id_a_nombre = {v: k for k, v in G1JointIndex.__dict__.items() if not k.startswith('__') and not callable(v)}

class ArmStateReader:
    def __init__(self):
        self.low_state = None
        self.first_update = False

    def init(self):
        self.subscriber = ChannelSubscriber("rt/lowstate", LowState_)
        self.subscriber.Init(self.lowstate_callback, 10)

    def lowstate_callback(self, msg: LowState_):
        self.low_state = msg
        self.first_update = True

    def get_joint_positions(self, joint_list):
        if self.low_state is None:
            return {}
        return {j: self.low_state.motor_state[j].q for j in joint_list}

def vista_previa_parcial(junta, pos, paso_idx):
    print(f"\nPaso {paso_idx + 1} ({junta}) capturado.")
    for motor_id in sorted(pos):
        nombre_mostrar = id_a_nombre.get(motor_id, f"Joint {motor_id}")
        valor_rad = pos[motor_id]
        valor_deg = math.degrees(valor_rad)
        print(f"  {nombre_mostrar:18}: {valor_rad:7.4f} rad ({valor_deg:6.2f} deg)")
    print()

def guardar_archivo(pasos):
    filename = input("Ingrese el nombre del archivo para guardar (ej: posiciones.txt): ").strip()
    if not filename.endswith(".txt"):
        filename += ".txt"
    with open(filename, 'w') as f:
        json.dump(pasos, f, indent=2)
    print(f"\nArchivo guardado exitosamente como '{filename}'.")

def eliminar_ultimo_paso(pasos):
    if pasos:
        eliminado = pasos.pop()
        print(f"Último paso eliminado: {eliminado[0]}")
    else:
        print("No hay pasos para eliminar.")

def grabar_modo_1(reader, pasos, contador):
    pos = reader.get_joint_positions(BRAZOS_Y_CINTURA)
    pasos.append((f"Paso {contador}", pos))
    vista_previa_parcial("todos los motores", pos, contador - 1)
    return contador + 1

def grabar_modo_2(reader, pasos, contador):
    pos_izq = reader.get_joint_positions(BRAZO_IZQ)
    pasos.append((f"Paso {contador}", pos_izq))
    vista_previa_parcial("brazo izquierdo", pos_izq, contador - 1)

    input(f"Captura brazo derecho para paso {contador}. Enter para continuar...")
    pos_der = reader.get_joint_positions(BRAZO_DER)
    pasos[-1][1].update(pos_der)
    vista_previa_parcial("brazo derecho", pos_der, contador - 1)

    grabar_cintura = input("¿Capturar cintura para este paso? [s/n]: ").strip().lower()
    if grabar_cintura == 's':
        pos_cintura = reader.get_joint_positions(CINTURA)
        pasos[-1][1].update(pos_cintura)
        vista_previa_parcial("cintura", pos_cintura, contador - 1)
    else:
        for j in CINTURA:
            pasos[-1][1][j] = 0.0

    return contador + 1

def grabar_modo_3(reader, pasos, contador):
    pos_izq = reader.get_joint_positions(BRAZO_IZQ)
    paso = {k: v for k, v in pos_izq.items()}
    for izq_id, (der_id, signo) in MIRROR_MAP.items():
        if izq_id in paso:
            paso[der_id] = paso[izq_id] * signo
    pasos.append((f"Paso {contador}", paso))
    vista_previa_parcial("brazo izquierdo + espejo derecho", paso, contador - 1)

    grabar_cintura = input("¿Capturar cintura para este paso? [s/n]: ").strip().lower()
    if grabar_cintura == 's':
        pos_cintura = reader.get_joint_positions(CINTURA)
        pasos[-1][1].update(pos_cintura)
        vista_previa_parcial("cintura", pos_cintura, contador - 1)
    else:
        for j in CINTURA:
            pasos[-1][1][j] = 0.0

    return contador + 1

def repetir_pasos(pasos, contador):
    try:
        n = int(input("¿Cuántos pasos anteriores quiere repetir?: "))
        veces = int(input("¿Cuántas veces desea repetirlos?: "))
        if n <= 0 or veces <= 0:
            print("Valores inválidos. Deben ser mayores a cero.")
            return contador
        if n > len(pasos):
            print("No hay suficientes pasos para repetir.")
            return contador
        seleccionados = pasos[-n:]
        for i in range(veces):
            for nombre, pos in seleccionados:
                nueva_pos = {k: v for k, v in pos.items()}
                pasos.append((f"Paso {contador}", nueva_pos))
                vista_previa_parcial("repetido", nueva_pos, contador - 1)
                contador += 1
    except ValueError:
        print("Entrada inválida. Asegúrese de ingresar números.")
    return contador

def main():
    if len(sys.argv) < 2:
        print(f"Uso: python3 {sys.argv[0]} <interfaz_red>")
        sys.exit(1)

    ChannelFactoryInitialize(0, sys.argv[1])
    reader = ArmStateReader()
    reader.init()

    print("Esperando conexión con el robot...")
    while not reader.first_update:
        time.sleep(0.1)
    print("Conexión establecida.")

    pasos = []
    contador = 1

    while True:
        print("\nMODOS DE CAPTURA DISPONIBLES:")
        print("  1: Grabar todos los motores.")
        print("  2: Capturar brazo izquierdo → derecho → cintura opcional.")
        print("  3: Capturar brazo izquierdo y generar espejo derecho.")
        print("  r: Repetir últimos pasos.")
        print("  e: Eliminar último paso.")
        print("  f: Finalizar y guardar.")

        modo = input("Seleccione un modo de grabación (1, 2, 3, r, e, f): ").strip().lower()

        if modo == '1':
            contador = grabar_modo_1(reader, pasos, contador)
        elif modo == '2':
            contador = grabar_modo_2(reader, pasos, contador)
        elif modo == '3':
            contador = grabar_modo_3(reader, pasos, contador)
        elif modo == 'r':
            contador = repetir_pasos(pasos, contador)
        elif modo == 'e':
            eliminar_ultimo_paso(pasos)
            contador = max(1, contador - 1)
        elif modo == 'f':
            break
        else:
            print("Modo no reconocido.")

    if pasos:
        guardar_archivo(pasos)
    else:
        print("No se capturaron pasos.")

if __name__ == "__main__":
    main()

