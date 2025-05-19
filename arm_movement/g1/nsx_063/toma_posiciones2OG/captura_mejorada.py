# Mejoras al script de captura de posiciones del Unitree G1
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
    15: (22, 1),  # Pitch
    16: (23, -1), # Roll
    17: (24, -1), # Yaw
    18: (25, 1),  # Elbow
    19: (26, -1), # Wrist Roll
    20: (27, 1),  # Wrist Pitch
    21: (28, -1)  # Wrist Yaw
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

def mostrar_vista_previa(pasos):
    print("\n--- Vista previa de posiciones capturadas ---\n")
    for i, (nombre, pos) in enumerate(pasos):
        print(f"{nombre}:")
        for motor_id in sorted(pos):
            nombre_mostrar = id_a_nombre.get(motor_id, f"Joint {motor_id}")
            valor_rad = pos[motor_id]
            valor_deg = math.degrees(valor_rad)
            print(f"  {nombre_mostrar:18}: {valor_rad:7.4f} rad ({valor_deg:6.2f} deg)")
        print()

def vista_previa_parcial(junta, pos, paso_idx):
    print(f"\nPaso {paso_idx + 1} ({junta}) capturado.")
    for motor_id in sorted(pos):
        nombre_mostrar = id_a_nombre.get(motor_id, f"Joint {motor_id}")
        valor_rad = pos[motor_id]
        valor_deg = math.degrees(valor_rad)
        print(f"  {nombre_mostrar:18}: {valor_rad:7.4f} rad ({valor_deg:6.2f} deg)")
    print()

def guardar_archivo(pasos):
    mostrar_vista_previa(pasos)
    confirmar = input("¿Desea guardar esta secuencia? [s/n]: ").strip().lower()
    if confirmar != 's':
        print("Secuencia descartada. No se guardó ningún archivo.")
        return

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

    print("\nMODOS DE CAPTURA DISPONIBLES:")
    print("  1: Grabar todos los motores en cada paso con 's'.")
    print("  2: Capturar brazo izquierdo, luego brazo derecho, luego cintura opcional.")
    print("  3: Capturar brazo izquierdo y generar automáticamente el espejo en brazo derecho.")

    modo = input("Seleccione un modo de grabación (1, 2 o 3): ").strip()
    pasos = []

    if modo == '1':
        step_counter = 1
        print("\nModo manual: Presione 's' para guardar, 'eliminar' para borrar el último paso, 'finalizar' para terminar.")
        while True:
            comando = input("Comando ('s', 'eliminar', 'finalizar'): ").strip().lower()
            if comando == 's':
                pos = reader.get_joint_positions(BRAZOS_Y_CINTURA)
                pasos.append((f"Paso {step_counter}", pos))
                vista_previa_parcial("todos los motores", pos, step_counter - 1)
                print(f"Paso guardado. Total: {step_counter} pasos.")
                step_counter += 1
            elif comando == 'eliminar':
                eliminar_ultimo_paso(pasos)
                step_counter = max(1, step_counter - 1)
            elif comando == 'finalizar':
                break
            else:
                print("Comando no reconocido.")

    elif modo == '2':
        print("\nGrabando posiciones para el brazo izquierdo. Presione Enter para capturar cada paso. Escriba 'finalizar' para terminar.")
        while True:
            entrada = input("Presione Enter para capturar paso, o escriba 'finalizar': ").strip().lower()
            if entrada == 'finalizar':
                break
            pos = reader.get_joint_positions(BRAZO_IZQ)
            pasos.append((f"Paso {len(pasos)+1}", pos))
            vista_previa_parcial("brazo izquierdo", pos, len(pasos)-1)
            print(f"Paso grabado. Le faltan {max(0, len(pasos))} para el brazo derecho.")

        if not pasos:
            print("No se capturaron pasos con el brazo izquierdo. Abortando.")
            return

        total_pasos = len(pasos)
        print(f"\nDebe grabar {total_pasos} pasos para el brazo derecho.")
        for i in range(total_pasos):
            input(f"Grabando paso {i+1}/{total_pasos} (brazo derecho). Presione Enter...")
            pos_derecho = reader.get_joint_positions(BRAZO_DER)
            pasos[i][1].update(pos_derecho)
            vista_previa_parcial("brazo derecho", pos_derecho, i)

        grabar_cintura = input("¿Desea capturar también posiciones de cintura? [s/n]: ").strip().lower()
        if grabar_cintura == 's':
            for i in range(total_pasos):
                input(f"Grabando paso {i+1}/{total_pasos} (cintura). Presione Enter...")
                cintura_data = reader.get_joint_positions(CINTURA)
                pasos[i][1].update(cintura_data)
                vista_previa_parcial("cintura", cintura_data, i)
        else:
            for paso in pasos:
                for j in CINTURA:
                    paso[1][j] = 0.0

    elif modo == '3':
        print("\nGrabando posiciones para el brazo izquierdo. El brazo derecho se generará automáticamente en espejo.")
        while True:
            entrada = input("Presione Enter para capturar paso, o escriba 'finalizar': ").strip().lower()
            if entrada == 'finalizar':
                break
            pos_izq = reader.get_joint_positions(BRAZO_IZQ)
            paso = {k: v for k, v in pos_izq.items()}
            for izq_id, (der_id, signo) in MIRROR_MAP.items():
                if izq_id in paso:
                    paso[der_id] = paso[izq_id] * signo
            pasos.append((f"Paso {len(pasos)+1}", paso))
            vista_previa_parcial("brazo izquierdo + espejo derecho", paso, len(pasos)-1)

        if not pasos:
            print("No se capturaron pasos. Abortando.")
            return

        total_pasos = len(pasos)
        grabar_cintura = input("¿Desea capturar también posiciones de cintura? [s/n]: ").strip().lower()
        if grabar_cintura == 's':
            for i in range(total_pasos):
                input(f"Grabando paso {i+1}/{total_pasos} (cintura). Presione Enter...")
                cintura_data = reader.get_joint_positions(CINTURA)
                pasos[i][1].update(cintura_data)
                vista_previa_parcial("cintura", cintura_data, i)
        else:
            for paso in pasos:
                for j in CINTURA:
                    paso[1][j] = 0.0

    else:
        print("Modo inválido. Terminando ejecución.")
        return

    if not pasos:
        print("No se capturaron pasos. Finalizando sin guardar.")
        return

    guardar_archivo(pasos)

if __name__ == "__main__":
    main()
