import sys
import time
import math

from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelPublisher, ChannelSubscriber
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

class ArmSequence:
    def __init__(self):
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

def main():
    if len(sys.argv) < 2:
        sys.exit("Uso: python3 saludo_militar.py <interfaz_red>")

    ChannelFactoryInitialize(0, sys.argv[1])
    seq = ArmSequence()
    seq.Init()
    seq.Start()
    #seq.move_to({joint: 0.0 for joint in seq.arm_joints})

    pasos = [
        ("Paso 1", {
            G1JointIndex.LeftShoulderPitch: 0.0,
            G1JointIndex.LeftShoulderRoll: 0.313,
            G1JointIndex.LeftShoulderYaw: 0.0,
            G1JointIndex.LeftElbow: 1.5,
            G1JointIndex.LeftWristRoll: 0.0,
            G1JointIndex.LeftWristPitch: 0.0,
            G1JointIndex.LeftWristYaw: 0.0,
            G1JointIndex.RightShoulderPitch: 0.0,
            G1JointIndex.RightShoulderRoll: -0.313,
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
            G1JointIndex.LeftShoulderRoll: 0.313,
            G1JointIndex.LeftShoulderYaw: 0.0,
            G1JointIndex.LeftElbow: 0.0,
            G1JointIndex.LeftWristRoll: 0.0,
            G1JointIndex.LeftWristPitch: 0.0,
            G1JointIndex.LeftWristYaw: 0.0,
            G1JointIndex.RightShoulderPitch: 0.0,
            G1JointIndex.RightShoulderRoll: -0.313,
            G1JointIndex.RightShoulderYaw: 0.0,
            G1JointIndex.RightElbow: 0.0,
            G1JointIndex.RightWristRoll: 0.0,
            G1JointIndex.RightWristPitch: 0.0,
            G1JointIndex.RightWristYaw: 0.0,
            G1JointIndex.WaistYaw: 0.0,
            G1JointIndex.WaistRoll: 0.0,
            G1JointIndex.WaistPitch: 0.0
        }),
        ("Paso 3", {
            G1JointIndex.LeftShoulderPitch: 0.0,
            G1JointIndex.LeftShoulderRoll: 0.313,
            G1JointIndex.LeftShoulderYaw: 0.0,
            G1JointIndex.LeftElbow: 0.0,
            G1JointIndex.LeftWristRoll: -1.7,
            G1JointIndex.LeftWristPitch: 0.0,
            G1JointIndex.LeftWristYaw: 0.0,
            G1JointIndex.RightShoulderPitch: 0.0,
            G1JointIndex.RightShoulderRoll: -0.313,
            G1JointIndex.RightShoulderYaw: 0.0,
            G1JointIndex.RightElbow: 0.0,
            G1JointIndex.RightWristRoll: 1.7,
            G1JointIndex.RightWristPitch: 0.0,
            G1JointIndex.RightWristYaw: 0.0,
            G1JointIndex.WaistYaw: 0.0,
            G1JointIndex.WaistRoll: 0.0,
            G1JointIndex.WaistPitch: 0.0
        }),
        ("Paso 4", {
            G1JointIndex.LeftShoulderPitch: 0.0,
            G1JointIndex.LeftShoulderRoll: 0.313,
            G1JointIndex.LeftShoulderYaw: -0.220,
            G1JointIndex.LeftElbow: 0.0,
            G1JointIndex.LeftWristRoll: -1.7,
            G1JointIndex.LeftWristPitch: 0.0,
            G1JointIndex.LeftWristYaw: 0.0,
            G1JointIndex.RightShoulderPitch: 0.0,
            G1JointIndex.RightShoulderRoll: -0.313,
            G1JointIndex.RightShoulderYaw: 0.220,
            G1JointIndex.RightElbow: 0.0,
            G1JointIndex.RightWristRoll: 1.7,
            G1JointIndex.RightWristPitch: 0.0,
            G1JointIndex.RightWristYaw: 0.0,
            G1JointIndex.WaistYaw: 0.0,
            G1JointIndex.WaistRoll: 0.0,
            G1JointIndex.WaistPitch: 0.0
        }),
        ("Paso 5", {
            G1JointIndex.LeftShoulderPitch: 0.0,
            G1JointIndex.LeftShoulderRoll: 0.313,
            G1JointIndex.LeftShoulderYaw: -0.220,
            G1JointIndex.LeftElbow: -0.513,
            G1JointIndex.LeftWristRoll: -1.79,
            G1JointIndex.LeftWristPitch: 0.0,
            G1JointIndex.LeftWristYaw: 0.371,
            G1JointIndex.RightShoulderPitch: 0.0,
            G1JointIndex.RightShoulderRoll: -0.313,
            G1JointIndex.RightShoulderYaw: 0.220,
            G1JointIndex.RightElbow: -0.513,
            G1JointIndex.RightWristRoll: 1.79,
            G1JointIndex.RightWristPitch: 0.0,
            G1JointIndex.RightWristYaw: -0.371,
            G1JointIndex.WaistYaw: 0.0,
            G1JointIndex.WaistRoll: 0.0,
            G1JointIndex.WaistPitch: 0.0
        }), #ACA VAMOS
        ("Paso 6", {
            G1JointIndex.LeftShoulderPitch: 0.0,
            G1JointIndex.LeftShoulderRoll: 0.313,
            G1JointIndex.LeftShoulderYaw: -0.220,
            G1JointIndex.LeftElbow: 0.0,
            G1JointIndex.LeftWristRoll: -1.7,
            G1JointIndex.LeftWristPitch: 0.0,
            G1JointIndex.LeftWristYaw: 0.0,
            G1JointIndex.RightShoulderPitch: 0.0,
            G1JointIndex.RightShoulderRoll: -0.313,
            G1JointIndex.RightShoulderYaw: 0.220,
            G1JointIndex.RightElbow: 0.0,
            G1JointIndex.RightWristRoll: 1.7,
            G1JointIndex.RightWristPitch: 0.0,
            G1JointIndex.RightWristYaw: 0.0,
            G1JointIndex.WaistYaw: 0.0,
            G1JointIndex.WaistRoll: 0.0,
            G1JointIndex.WaistPitch: 0.0
        }),
        ("Paso 7", {
            G1JointIndex.LeftShoulderPitch: 0.0,
            G1JointIndex.LeftShoulderRoll: 0.313,
            G1JointIndex.LeftShoulderYaw: 0.0,
            G1JointIndex.LeftElbow: 0.0,
            G1JointIndex.LeftWristRoll: -1.7,
            G1JointIndex.LeftWristPitch: 0.0,
            G1JointIndex.LeftWristYaw: 0.0,
            G1JointIndex.RightShoulderPitch: 0.0,
            G1JointIndex.RightShoulderRoll: -0.313,
            G1JointIndex.RightShoulderYaw: 0.0,
            G1JointIndex.RightElbow: 0.0,
            G1JointIndex.RightWristRoll: 1.7,
            G1JointIndex.RightWristPitch: 0.0,
            G1JointIndex.RightWristYaw: 0.0,
            G1JointIndex.WaistYaw: 0.0,
            G1JointIndex.WaistRoll: 0.0,
            G1JointIndex.WaistPitch: 0.0
        }),
        ("Paso 8", {
            G1JointIndex.LeftShoulderPitch: 0.0,
            G1JointIndex.LeftShoulderRoll: 0.313,
            G1JointIndex.LeftShoulderYaw: 0.0,
            G1JointIndex.LeftElbow: 0.0,
            G1JointIndex.LeftWristRoll: 0.0,
            G1JointIndex.LeftWristPitch: 0.0,
            G1JointIndex.LeftWristYaw: 0.0,
            G1JointIndex.RightShoulderPitch: 0.0,
            G1JointIndex.RightShoulderRoll: -0.313,
            G1JointIndex.RightShoulderYaw: 0.0,
            G1JointIndex.RightElbow: 0.0,
            G1JointIndex.RightWristRoll: 0.0,
            G1JointIndex.RightWristPitch: 0.0,
            G1JointIndex.RightWristYaw: 0.0,
            G1JointIndex.WaistYaw: 0.0,
            G1JointIndex.WaistRoll: 0.0,
            G1JointIndex.WaistPitch: 0.0
        }),
        ("Paso 9", {
            G1JointIndex.LeftShoulderPitch: 0.0,
            G1JointIndex.LeftShoulderRoll: 0.313,
            G1JointIndex.LeftShoulderYaw: 0.0,
            G1JointIndex.LeftElbow: 1.5,
            G1JointIndex.LeftWristRoll: 0.0,
            G1JointIndex.LeftWristPitch: 0.0,
            G1JointIndex.LeftWristYaw: 0.0,
            G1JointIndex.RightShoulderPitch: 0.0,
            G1JointIndex.RightShoulderRoll: -0.313,
            G1JointIndex.RightShoulderYaw: 0.0,
            G1JointIndex.RightElbow: 1.5,
            G1JointIndex.RightWristRoll: 0.0,
            G1JointIndex.RightWristPitch: 0.0,
            G1JointIndex.RightWristYaw: 0.0,
            G1JointIndex.WaistYaw: 0.0,
            G1JointIndex.WaistRoll: 0.0,
            G1JointIndex.WaistPitch: 0.0
        }),
    ]

    for i, paso in enumerate(pasos):
        #input(f"{i} ... {paso[0]}")

        seq.move_to(paso[1])

        '''if i == 3:
            seq.move_to(paso[1], duration=0.5)
        elif i == 5:
            seq.move_to(paso[1], duration=2)
        else:
            seq.move_to(paso[1])'''
        if i == 4:
            time.sleep(10)

if __name__ == "__main__":
    main()
