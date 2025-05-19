"""
@file g1_autonomousV1.py
@author Sofía Milagros Castaño Vanegas - Robotics 4.0 Team
@date 2025-04-21
@version 1.0
@brief Navegación preconfigurada del robot G1 de Unitree utilizando SDK2.

"""

import time
import math
from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient
from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelSubscriber, ChannelPublisher
from unitree_sdk2py.idl.unitree_go.msg.dds_ import SportModeState_
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_, LowState_
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_
from unitree_sdk2py.utils.crc import CRC
from unitree_sdk2py.utils.thread import RecurrentThread
import sys

class G1JointIndex:
    LeftHipPitch = 0
    LeftHipRoll = 1
    LeftHipYaw = 2
    LeftKnee = 3
    LeftAnklePitch = 4
    LeftAnkleB = 4
    LeftAnkleRoll = 5
    LeftAnkleA = 5

    # Pierna derecha
    RightHipPitch = 6
    RightHipRoll = 7
    RightHipYaw = 8
    RightKnee = 9
    RightAnklePitch = 10
    RightAnkleB = 10
    RightAnkleRoll = 11
    RightAnkleA = 11

    # Cintura
    WaistYaw = 12
    WaistRoll = 13        # No válido para G1 23DoF/29DoF con cintura bloqueada
    WaistA = 13           # No válido para G1 23DoF/29DoF con cintura bloqueada
    WaistPitch = 14       # No válido para G1 23DoF/29DoF con cintura bloqueada
    WaistB = 14           # No válido para G1 23DoF/29DoF con cintura bloqueada

    # Brazo izquierdo
    LeftShoulderPitch = 15
    LeftShoulderRoll = 16
    LeftShoulderYaw = 17
    LeftElbow = 18
    LeftWristRoll = 19
    LeftWristPitch = 20   # No válido para G1 23DoF
    LeftWristYaw = 21     # No válido para G1 23DoF

    # Brazo derecho
    RightShoulderPitch = 22
    RightShoulderRoll = 23
    RightShoulderYaw = 24
    RightElbow = 25
    RightWristRoll = 26
    RightWristPitch = 27  # No válido para G1 23DoF
    RightWristYaw = 28    # No válido para G1 23DoF

    kNotUsedJoint = 29  # Articulación no utilizada (peso)


class G1TrajectoryExecutor:
    def __init__(self, interface):
        ChannelFactoryInitialize(0, interface)
        self.client = LocoClient()
        self.client.SetTimeout(10.0)
        self.client.Init()
        
        self.control_dt = 0.02
        self.kp = 60.0
        self.kd = 1.5
        self.crc = CRC()
        self.t = 0.0
        self.T = 3.0
        self.low_cmd = unitree_hg_msg_dds__LowCmd_()
        self.low_state = None
        self.first_update = False
        self.target_pos = {}
        self.arm_joints = [
            G1JointIndex.LeftShoulderPitch,  G1JointIndex.LeftShoulderRoll,
            G1JointIndex.LeftShoulderYaw,    G1JointIndex.LeftElbow,
            G1JointIndex.LeftWristRoll,      G1JointIndex.LeftWristPitch,
            G1JointIndex.LeftWristYaw,
            G1JointIndex.RightShoulderPitch, G1JointIndex.RightShoulderRoll,
            G1JointIndex.RightShoulderYaw,   G1JointIndex.RightElbow,
            G1JointIndex.RightWristRoll,     G1JointIndex.RightWristPitch,
            G1JointIndex.RightWristYaw,
            G1JointIndex.WaistYaw,
            G1JointIndex.WaistRoll,
            G1JointIndex.WaistPitch
        ]
        # Pares: (nombre, diccionario de posiciones articulares)
        self.pasos = [
            ("Paso 1", {
            G1JointIndex.LeftShoulderPitch: 0.0,
            G1JointIndex.LeftShoulderRoll: 0.35,
            G1JointIndex.LeftShoulderYaw: 0.0,
            G1JointIndex.LeftElbow: 1.5,
            G1JointIndex.LeftWristRoll: 0.0,
            G1JointIndex.LeftWristPitch: 0.0,
            G1JointIndex.LeftWristYaw: 0.0,
            G1JointIndex.RightShoulderPitch: 0.0,
            G1JointIndex.RightShoulderRoll: -0.35,
            G1JointIndex.RightShoulderYaw: 0.0,
            G1JointIndex.RightElbow: 1.5,
            G1JointIndex.RightWristRoll: 0.0,
            G1JointIndex.RightWristPitch: 0.0,
            G1JointIndex.RightWristYaw: 0.0,
            G1JointIndex.WaistYaw: 0.0,
            G1JointIndex.WaistRoll: 0.0,
            G1JointIndex.WaistPitch: 0.0
        }),
        ("Paso 2", {
            
            
            G1JointIndex.LeftShoulderPitch: 0.0,
            G1JointIndex.LeftShoulderRoll: 0.35,
            G1JointIndex.LeftShoulderYaw: 0.4,
            G1JointIndex.LeftElbow: -0.1,
            G1JointIndex.LeftWristRoll: 0.0,
            G1JointIndex.LeftWristPitch: 0.0,
            G1JointIndex.LeftWristYaw: 0.0,
            G1JointIndex.RightShoulderPitch: 0.0,
            G1JointIndex.RightShoulderRoll: -0.35,
            G1JointIndex.RightShoulderYaw: -0.4,
            G1JointIndex.RightElbow: -0.1,
            G1JointIndex.RightWristRoll: 0.0,
            G1JointIndex.RightWristPitch: 0.0,
            G1JointIndex.RightWristYaw: 0.0,
            G1JointIndex.WaistYaw: 0.0,
            G1JointIndex.WaistRoll: 0.0,
            G1JointIndex.WaistPitch: 0.0
        }),

        ("Paso 3", {
            G1JointIndex.LeftShoulderPitch: 0.0,
            G1JointIndex.LeftShoulderRoll: 0.35,
            G1JointIndex.LeftShoulderYaw: -0.2,
            G1JointIndex.LeftElbow: -0.1,
            G1JointIndex.LeftWristRoll: 0.0,
            G1JointIndex.LeftWristPitch: 0.0,
            G1JointIndex.LeftWristYaw: 0.0,
            G1JointIndex.RightShoulderPitch: 0.0,
            G1JointIndex.RightShoulderRoll: -0.35,
            G1JointIndex.RightShoulderYaw: 0.2,
            G1JointIndex.RightElbow: -0.1,
            G1JointIndex.RightWristRoll: 0.0,
            G1JointIndex.RightWristPitch: 0.0,
            G1JointIndex.RightWristYaw: 0.0,
            G1JointIndex.WaistYaw: 0.0,
            G1JointIndex.WaistRoll: 0.0,
            G1JointIndex.WaistPitch: 0.0
            
        }),
        ]
        
    def Init(self):
        self.publisher = ChannelPublisher("rt/arm_sdk", LowCmd_)
        self.publisher.Init()
        self.subscriber = ChannelSubscriber("rt/lowstate", LowState_)
        self.subscriber.Init(self.LowStateHandler, 10)

    def Start(self):
        self.thread = RecurrentThread(interval=self.control_dt, target=self.LowCmdWrite, name="arm_control")
        while not self.first_update:
            time.sleep(0.1)
        self.thread.Start()

    def LowStateHandler(self, msg: LowState_):
        self.low_state = msg
        if not self.first_update:
            self.first_update = True

    def interpolate_position(self, q_init, q_target):
        ratio = (1 - math.cos(math.pi * (self.t / self.T))) / 2 if self.t < self.T else 1.0
        return q_init + (q_target - q_init) * ratio
    
    def LowCmdWrite(self):
        if self.low_state is None:
            return

        self.low_cmd.motor_cmd[G1JointIndex.kNotUsedJoint].q = 1  # Enable arm_sdk

        for joint in self.arm_joints:
            q_init = self.low_state.motor_state[joint].q
            q_target = self.target_pos.get(joint, q_init)
            pos = self.interpolate_position(q_init, q_target)
            self.low_cmd.motor_cmd[joint].q = pos
            self.low_cmd.motor_cmd[joint].dq = 0.0
            self.low_cmd.motor_cmd[joint].tau = 0.0
            self.low_cmd.motor_cmd[joint].kp = self.kp
            self.low_cmd.motor_cmd[joint].kd = self.kd

        self.low_cmd.crc = self.crc.Crc(self.low_cmd)
        self.publisher.Write(self.low_cmd)
        self.t += self.control_dt
        
    def move_to(self, updates: dict, duration=1.0):
            self.target_pos.update(updates)
            self.T = duration
            self.t = 0.0

            # Esperar hasta completar interpolación
            while self.t < self.T:
                time.sleep(self.control_dt)
            #    self.t = self.t + self.control_dt

    def move(self, x_vel=0.0, y_vel=0.0, yaw_vel=0.0, duration=2.0):
        """
        Ejecuta un movimiento de velocidades específicas por un tiempo determinado.
        """
        self.client.Move(x_vel, y_vel, yaw_vel, True)
        time.sleep(duration)
        self.client.Move(0, 0, 0)
        time.sleep(1.0)

    def shutdown(self):
            """
            Detiene completamente al robot de manera segura.
            """
            self.client.Move(0, 0, 0)
            self.client.StopMove()
            self.running = False
            print("Robot detenido correctamente.")

def main():
    if len(sys.argv) < 2:
        print(f"Uso: python3 {sys.argv[0]} networkInterface")
        sys.exit(1)

    print("\n Asegúrate de que no haya obstáculos alrededor del robot.")
    input("Presiona Enter cuando el área esté despejada...")

    try:
        robot = G1TrajectoryExecutor(sys.argv[1])
        robot.Init()
        robot.Start()
        # Lista de movimientos: (x_vel, y_vel, yaw_vel, duración)
        movimientos = [
            (0.4, 0.0, 0.0, 3.0),     # Paso 1 Avanza hasta antes de la caja
            (0.4, 0.0, 0.0, 1.0),    # Paso 2  Termina de llegar a la caja
            (-0.4, 0.0, 0.0, 2.0),     # Paso 3 Retrocede un poco
            (0.0, 0.0, -0.5, 3.14),    # Paso 4 Gira 90 grados
            (0.4, 0.0, 0.0, 3.0),     # Paso 5 Avanza
            (0.0, 0.0, 0.5, 3.14),     # Paso 6 Gira 90 grados
            (0.4, 0.0, 0.0, 2.0),       #Paso 7 Llega a punto B de la caja
            (-0.4, 0.0, 0.0, 1.0),       #Paso 7 Llega a punto B de la caja
            (0.0, 0.0, 0.5, 4.1),       #Paso 7 Llega a punto B de la caja
            (0.4, 0.0, 0.0, 2.5),       #Paso 7 Llega a punto B de la caja
            (0.0, 0.0, -0.5, 4.1)       #Paso 7 Llega a punto B de la caja

        ]

        # Ejecutar paso antes de iniciar movimiento
        print("\n>> Ejecutando paso previo al movimiento: Paso 1 (inicio)")
        robot.move_to(robot.pasos[0][1], duration=1.5)

        for i, mov in enumerate(movimientos):
            print(f"\n>> Movimiento {i+1}")
            robot.move(*mov)

            # if i < len(robot.pasos):
            #     print(f">> Ejecutando postura: {robot.pasos[i][0]}")
            #     robot.move_to(robot.pasos[i][1], duration=1.5)
            
            if i == 0:
                print(">> Ejecutando paso adicional después del paso 2: Paso 2")
                robot.move_to(robot.pasos[1][1], duration=1.5)

            # ejecutar paso extra después del paso 2
            if i == 1:
                print(">> Ejecutando paso adicional después del paso 2: Paso 3")
                robot.move_to(robot.pasos[2][1], duration=1.5)

            # ejecutar paso extra después del paso 7
            if i == 6:
                print(">> Ejecutando paso final después del paso 7: Paso 2")
                robot.move_to(robot.pasos[1][1], duration=1.5)
            
            if i == 7:
                print(">> Ejecutando paso final después del paso 7: Paso 2")
                robot.move_to(robot.pasos[0][1], duration=1.5)

        print("\nTrayectoria completa.")
    
    except KeyboardInterrupt:
        print("\nPrograma interrumpido por el usuario.")
    except Exception as e:
        print(f"\nError: {str(e)}")
    finally:
        try:
            robot.shutdown()
        except Exception as e:
            print(f"\nError al detener el robot: {str(e)}")


if __name__ == "__main__":
    main()
