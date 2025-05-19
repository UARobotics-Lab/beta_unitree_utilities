import sys
import time
import math
import json
from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelSubscriber
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_

# Definimos los índices de articulaciones directamente
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

# Solo estos motores se usan
motores_usados = [
    G1JointIndex.LeftShoulderPitch, G1JointIndex.LeftShoulderRoll,
    G1JointIndex.LeftShoulderYaw, G1JointIndex.LeftElbow,
    G1JointIndex.LeftWristRoll, G1JointIndex.LeftWristPitch,
    G1JointIndex.LeftWristYaw,
    G1JointIndex.RightShoulderPitch, G1JointIndex.RightShoulderRoll,
    G1JointIndex.RightShoulderYaw, G1JointIndex.RightElbow,
    G1JointIndex.RightWristRoll, G1JointIndex.RightWristPitch,
    G1JointIndex.RightWristYaw,
    G1JointIndex.WaistYaw,
    G1JointIndex.WaistRoll,
    G1JointIndex.WaistPitch
]

# Diccionario que mapea ID a nombre de atributo
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
        if not self.first_update:
            self.first_update = True

    def get_joint_positions(self):
        if self.low_state is None:
            return {}

        joint_positions = {}
        for joint_id in motores_usados:
            joint_positions[joint_id] = self.low_state.motor_state[joint_id].q  # Guardamos como número
        return joint_positions

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
    print("\nControles:")
    print(" - Escriba 's' y presione Enter para guardar la posición actual.")
    print(" - Escriba 'a' y presione Enter para mostrar la posición actual (sin guardar).")
    print(" - Escriba 'finalizar' y presione Enter para terminar y guardar el archivo.\n")

    saved_positions = []
    step_counter = 1

    # Orden lógico de impresión
    orden_logico = [
        G1JointIndex.LeftShoulderPitch, G1JointIndex.LeftShoulderRoll, G1JointIndex.LeftShoulderYaw,
        G1JointIndex.LeftElbow, G1JointIndex.LeftWristRoll, G1JointIndex.LeftWristPitch, G1JointIndex.LeftWristYaw,
        G1JointIndex.RightShoulderPitch, G1JointIndex.RightShoulderRoll, G1JointIndex.RightShoulderYaw,
        G1JointIndex.RightElbow, G1JointIndex.RightWristRoll, G1JointIndex.RightWristPitch, G1JointIndex.RightWristYaw,
        G1JointIndex.WaistYaw, G1JointIndex.WaistRoll, G1JointIndex.WaistPitch
    ]

    while True:
        user_input = input("Ingrese comando ('s' guardar, 'a' mostrar actual, 'finalizar' terminar): ").strip().lower()

        if user_input == 's':
            pos = reader.get_joint_positions()
            paso_nombre = f"Paso {step_counter}"
            saved_positions.append((paso_nombre, pos))
            print(f"\nPosición {paso_nombre} guardada.")
            print("Contenido capturado:\n")

            for motor_id in orden_logico:
                if motor_id in pos:
                    valor_rad = pos[motor_id]
                    valor_deg = math.degrees(valor_rad)
                    nombre_mostrar = id_a_nombre[motor_id]
                    print(f"  {nombre_mostrar}: {valor_rad:.4f} rad ({valor_deg:.2f} deg)")

            print("\n")
            step_counter += 1

        elif user_input == 'a':
            pos = reader.get_joint_positions()
            print("\nPosición actual del robot (sin guardar):\n")

            for motor_id in orden_logico:
                if motor_id in pos:
                    valor_rad = pos[motor_id]
                    valor_deg = math.degrees(valor_rad)
                    nombre_mostrar = id_a_nombre[motor_id]
                    print(f"  {nombre_mostrar}: {valor_rad:.4f} rad ({valor_deg:.2f} deg)")

            print("\n")

        elif user_input == 'finalizar':
            break
        else:
            print("Entrada no válida. Escriba 's', 'a' o 'finalizar'.")

    # Preguntar nombre de archivo
    filename = input("Ingrese el nombre del archivo para guardar (ej: posiciones_guardadas.txt): ").strip()
    if not filename.endswith(".txt"):
        filename += ".txt"

    with open(filename, 'w') as f:
        json.dump(saved_positions, f, indent=2)

    print(f"\nArchivo guardado exitosamente como '{filename}'.")

if __name__ == "__main__":
    main()
