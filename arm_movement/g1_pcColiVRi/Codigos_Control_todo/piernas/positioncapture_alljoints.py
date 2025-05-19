import sys
import time
import math
import json
from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelSubscriber
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_

G1_NUM_MOTOR = 29

class G1JointIndex:
    LeftHipPitch = 0
    LeftHipRoll = 1
    LeftHipYaw = 2
    LeftKnee = 3
    LeftAnklePitch = 4
    LeftAnkleB = 4
    LeftAnkleRoll = 5
    LeftAnkleA = 5
    RightHipPitch = 6
    RightHipRoll = 7
    RightHipYaw = 8
    RightKnee = 9
    RightAnklePitch = 10
    RightAnkleB = 10
    RightAnkleRoll = 11
    RightAnkleA = 11
    WaistYaw = 12
    WaistRoll = 13        # NOTE: INVALID for g1 23dof/29dof with waist locked
    WaistA = 13           # NOTE: INVALID for g1 23dof/29dof with waist locked
    WaistPitch = 14       # NOTE: INVALID for g1 23dof/29dof with waist locked
    WaistB = 14           # NOTE: INVALID for g1 23dof/29dof with waist locked
    LeftShoulderPitch = 15
    LeftShoulderRoll = 16
    LeftShoulderYaw = 17
    LeftElbow = 18
    LeftWristRoll = 19
    LeftWristPitch = 20   # NOTE: INVALID for g1 23dof
    LeftWristYaw = 21     # NOTE: INVALID for g1 23dof
    RightShoulderPitch = 22
    RightShoulderRoll = 23
    RightShoulderYaw = 24
    RightElbow = 25
    RightWristRoll = 26
    RightWristPitch = 27  # NOTE: INVALID for g1 23dof
    RightWristYaw = 28    # NOTE: INVALID for g1 23dof

G1Joints={v: k for k, v in G1JointIndex.__dict__.items() if not k.startswith('__') and not callable(v)}


class ReadAllJoints:
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
        for joint_id in G1Joints:
            joint_positions[joint_id] = self.low_state.motor_state[joint_id].q  # Guardamos como número
        return joint_positions


def main():
    if len(sys.argv) < 2:
        print(f"Uso: python3 {sys.argv[0]} <interfaz_red>")
        sys.exit(1)

    if len(sys.argv)>1:
        ChannelFactoryInitialize(0, sys.argv[1])
    else:
        ChannelFactoryInitialize(0)

    reader = ReadAllJoints()
    reader.init()

    print("Esperando conexión con el robot...")
    while not reader.first_update:
        time.sleep(0.1)
    print("Conexión establecida.")

    saved_positions = []
    step_counter = 1

    while True:
        user_input = input("- 's' Guardar - 'a' Ver - 'end' Finalizar: ").strip().lower()

        if user_input == 's':
            pos = reader.get_joint_positions()
            paso_nombre = f"Paso {step_counter}"
            saved_positions.append((paso_nombre, pos))
            step_counter += 1
            print(f"\nPosición {paso_nombre} guardada.")
            print("\n")
            for i in range(G1_NUM_MOTOR):
                valor_rad = pos[i]
                print(f"  {G1Joints[i]}: {valor_rad:.4f} rad ({math.degrees(valor_rad):.2f} deg)")
            print("\n")

        elif user_input == 'a':
            print("\nPosición actual del robot:\n")
            for i in range(G1_NUM_MOTOR):
                valor_rad = pos[i]
                print(f"  {G1Joints[i]}: {valor_rad:.4f} rad ({math.degrees(valor_rad):.2f} deg)")
            print("\n")

        elif user_input == 'end':
            break
        else:
            print("\n")

    # Preguntar nombre de archivo
    filename = input("Ingrese el nombre del archivo (.txt): ").strip()
    if not filename.endswith(".txt"):
        filename += ".txt"

    with open(filename, 'w') as f:
        json.dump(saved_positions, f, indent=2)

    print(f"\nArchivo guardado como '{filename}'.")

if __name__ == "__main__":
    main()
