#!/usr/bin/env python3
"""
@file g1_autonomousV1.py
@author Sofía Milagros Castaño Vanegas - Robotics 4.0 Team
@date 2025-04-21
@version 1.0
@brief Movimiento de figuras con movimientos articulares
del robot G1 de Unitree utilizando SDK2.

"""

import sys
import time
import math
from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelPublisher, ChannelSubscriber
from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_, LowState_
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_
from unitree_sdk2py.utils.crc import CRC
from unitree_sdk2py.utils.thread import RecurrentThread


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

class MovementFlagDemo:
    def __init__(self, interface):
        """
        Constructor: inicializa conexión con el robot.
        """
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
        
        self.pasos = [
        ("Paso 1", {
            G1JointIndex.LeftShoulderPitch: 0.0,
            G1JointIndex.LeftShoulderRoll: 0.37,
            G1JointIndex.LeftShoulderYaw: 0.0,
            G1JointIndex.LeftElbow: 0.96,
            G1JointIndex.LeftWristRoll: 0.0,
            G1JointIndex.LeftWristPitch: 0.0,
            G1JointIndex.LeftWristYaw: 0.0,
            G1JointIndex.RightShoulderPitch: -0.41,
            G1JointIndex.RightShoulderRoll: -0.30,
            G1JointIndex.RightShoulderYaw: 0.3,
            G1JointIndex.RightElbow: -0.35,
            G1JointIndex.RightWristRoll: -0.7,
            G1JointIndex.RightWristPitch: -0.10,
            G1JointIndex.RightWristYaw: 0.0,
            G1JointIndex.WaistYaw: 0.0,
            G1JointIndex.WaistRoll: 0.0,
            G1JointIndex.WaistPitch: 0.0
        }),
        ("Paso 2", {
            G1JointIndex.LeftShoulderPitch: 0.0,
            G1JointIndex.LeftShoulderRoll: 0.37,
            G1JointIndex.LeftShoulderYaw: 0.0,
            G1JointIndex.LeftElbow: 0.96,
            G1JointIndex.LeftWristRoll: 0.0,
            G1JointIndex.LeftWristPitch: 0.0,
            G1JointIndex.LeftWristYaw: 0.0,
            G1JointIndex.RightShoulderPitch: -0.41,
            G1JointIndex.RightShoulderRoll: -0.30,
            G1JointIndex.RightShoulderYaw: -0.86,
            G1JointIndex.RightElbow: 0.71,
            G1JointIndex.RightWristRoll: -0.7,
            G1JointIndex.RightWristPitch: -0.10,
            G1JointIndex.RightWristYaw: 0.0,
            G1JointIndex.WaistYaw: 0.0,
            G1JointIndex.WaistRoll: 0.0,
            G1JointIndex.WaistPitch: 0.0
        })
    ]
        self.oscillating = False
        self.last_osc_time = 0.0
        self.current_osc_target = 0  # 0 o 1
        
        self.running = True
        

    def Init(self):
        # """
        # Pone al robot de pie y listo para moverse.
        # """
        # print("Iniciando robot...")
        # self.client.Damp()
        # time.sleep(1.0)
        # self.client.StandUp()
        # time.sleep(3.0)
        # print("Iniciando el robot, por favor presiona R1 + X en el control...")
        # time.sleep(7.0)
        # print("Robot listo para moverse.")
        
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
                
        
    def lower_flag(self, down_pose: dict = None, duration: float = 2.0):
        """Baja la bandera suavemente."""

        # Definir pose por defecto si no se pasa
        if down_pose is None:
            down_pose = {
                G1JointIndex.LeftShoulderPitch: 0.0,
                G1JointIndex.LeftShoulderRoll: 0.22,
                G1JointIndex.LeftShoulderYaw: 0.0,
                G1JointIndex.LeftElbow: 1.0,
                G1JointIndex.LeftWristRoll: 0.0,
                G1JointIndex.LeftWristPitch: 0.0,
                G1JointIndex.LeftWristYaw: 0.0,
                G1JointIndex.RightShoulderPitch: 0.0,
                G1JointIndex.RightShoulderRoll: -0.22,
                G1JointIndex.RightShoulderYaw: 0.0,
                G1JointIndex.RightElbow: 1.0,
                G1JointIndex.RightWristRoll: 0.0,
                G1JointIndex.RightWristPitch: 0.0,
                G1JointIndex.RightWristYaw: 0.0,
                G1JointIndex.WaistYaw: 0.0,
                G1JointIndex.WaistRoll: 0.0,
                G1JointIndex.WaistPitch: 0.0
            }

        # Ejecutar movimiento
        self.move_to(down_pose, duration=duration)
              

    def move_in_circle(self, speed_linear=0.4, speed_angular=0.5, duration=12.0):
        """
        Realiza un movimiento en círculo con oscilación de brazos embebida.
        """
        paso1 = self.pasos[0][1]
        paso2 = self.pasos[1][1]
        print("Iniciando movimiento en círculo...")

        # Inicia oscilación embebida
        oscillating = True
        current_osc_target = 0
        last_osc_time = time.time()
        osc_duration = 1.5

        self.move_to(paso1, duration=osc_duration)  # Paso inicial
        self.client.Move(speed_linear, 0.0, speed_angular, True)

        start_time = time.time()
        while time.time() - start_time < duration:
            now = time.time()
            if oscillating and (now - last_osc_time >= osc_duration):
                if current_osc_target == 0:
                    self.move_to(paso2, duration=osc_duration)
                    current_osc_target = 1
                else:
                    self.move_to(paso1, duration=osc_duration)
                    current_osc_target = 0
                last_osc_time = now
            time.sleep(0.02)

        self.client.Move(0, 0, 0)
        self.lower_flag()
        self.client.StopMove()


    def move_in_triangle(self, side_duration=3.0, rotation_speed=0.5):
        """
        Realiza un movimiento en triángulo equilátero con oscilación de brazos embebida.
        """
        paso1 = self.pasos[0][1]
        paso2 = self.pasos[1][1]
        print("Iniciando movimiento en triángulo...")

        # Parámetros de oscilación
        oscillating = True
        current_osc_target = 0
        last_osc_time = time.time()
        osc_duration = 1.5

        self.move_to(paso1, duration=osc_duration)  # Paso inicial

        for _ in range(3):
            start_time = time.time()
            self.client.Move(0.4, 0.0, 0.0, True)  # Avance recto
            while time.time() - start_time < side_duration:
                now = time.time()
                if oscillating and (now - last_osc_time >= osc_duration):
                    if current_osc_target == 0:
                        self.move_to(paso2, duration=osc_duration)
                        current_osc_target = 1
                    else:
                        self.move_to(paso1, duration=osc_duration)
                        current_osc_target = 0
                    last_osc_time = now
                time.sleep(0.02)

            self.client.Move(0, 0, 0)
            time.sleep(0.2)

            # Giro para formar el triángulo equilátero
            angle = (2 * math.pi / 3)
            rotation_duration = angle / abs(rotation_speed)
            start_time = time.time()
            self.client.Move(0.0, 0.0, -rotation_speed, True)
            while time.time() - start_time < rotation_duration:
                now = time.time()
                if oscillating and (now - last_osc_time >= osc_duration):
                    if current_osc_target == 0:
                        self.move_to(paso2, duration=osc_duration)
                        current_osc_target = 1
                    else:
                        self.move_to(paso1, duration=osc_duration)
                        current_osc_target = 0
                    last_osc_time = now
                time.sleep(0.02)

            self.client.Move(0, 0, 0)
            time.sleep(0.2)

        self.lower_flag()
        self.client.StopMove()

    

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
        robot = MovementFlagDemo(sys.argv[1])
        robot.Init()
        robot.Start()

        print("\nSelecciona la figura que quieres realizar:")
        print("1. Círculo")
        print("2. Triángulo")
        choice = input("Ingresa 1 o 2: ").strip()

        if choice == "1":
            robot.move_in_circle()
        elif choice == "2":
            robot.move_in_triangle()
        else:
            print("Opción no válida. No se ejecuta ningún movimiento.")

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
