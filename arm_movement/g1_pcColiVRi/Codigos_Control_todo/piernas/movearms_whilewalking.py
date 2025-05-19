import sys
import time
import math
import json
import numpy as np
import tty
import termios


from unitree_sdk2py.core.channel import ChannelPublisher, ChannelFactoryInitialize
from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowState_
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_
from unitree_sdk2py.utils.crc import CRC
from unitree_sdk2py.utils.thread import RecurrentThread
from unitree_sdk2py.comm.motion_switcher.motion_switcher_client import MotionSwitcherClient
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient




# Configuration constants
FORWARD_SPEED = 0.4     # Forward/backward speed in m/s
LATERAL_SPEED = 0.3     # Left/right speed in m/s
ROTATION_SPEED = 0.5    # Rotation speed in rad/s
STARTUP_DELAY = 3.0     # Delay after standing up in seconds
INIT_DELAY = 1.0        # Delay after initialization in seconds
COMMAND_DELAY = 2.0     # Delay after starting in seconds


G1_NUM_MOTOR = 29
ARM_INDEXES=[i for i in range(12,G1_NUM_MOTOR)]

POSICION1={0: 0.08999839425086975, 1: 0.034846872091293335, 2: 0.0301058292388916, 3: 0.08406209945678711, 4: -0.23287688195705414, 5: -0.1640467494726181, 6: 0.11192145943641663, 7: 0.09046268463134766, 8: 0.16595101356506348, 9: 0.07386088371276855, 10: -0.17216570675373077, 11: 0.013635979034006596, 12: 0.15062838792800903, 13: 0.0, 14: 0.0, 15: 0.17569327354431152, 16: 0.4680781364440918, 17: 0.7024753093719482, 18: -0.23448729515075684, 19: -0.4591975212097168, 20: 0.10223865509033203, 21: -0.11934280395507812, 22: 0.3019833564758301, 23: -0.49311304092407227, 24: -0.665036678314209, 25: 1.1438422203063965, 26: -0.5855154991149902, 27: -0.39355897903442383, 28: 0.020769119262695312}

POSICION2={0: 0.08267298340797424, 1: 0.035733312368392944, 2: 0.03006577491760254, 3: 0.08409619331359863, 4: -0.23286785185337067, 5: -0.16403204202651978, 6: 0.11273828148841858, 7: 0.08967018127441406, 8: 0.16707587242126465, 9: 0.07221627235412598, 10: -0.172170028090477, 11: 0.013643075712025166, 12: 0.15143191814422607, 13: 0.0, 14: 0.0, 15: 0.3386068344116211, 16: 0.47049903869628906, 17: 0.11956262588500977, 18: 0.9805333614349365, 19: 0.16356277465820312, 20: -0.4194760322570801, 21: -0.21259355545043945, 22: 0.08707022666931152, 23: -0.3454318046569824, 24: -0.6341891288757324, 25: 0.02308940887451172, 26: 0.004216194152832031, 27: -0.20110559463500977, 28: 0.0018782615661621094}

Kp = [
    60, 60, 60, 100, 40, 40,      # legs
    60, 60, 60, 100, 40, 40,      # legs
    60, 40, 40,                   # waist
    40, 40, 40, 40,  40, 40, 40,  # arms
    40, 40, 40, 40,  40, 40, 40   # arms
]

Kd = [
    1, 1, 1, 2, 1, 1,     # legs
    1, 1, 1, 2, 1, 1,     # legs
    1, 1, 1,              # waist
    1, 1, 1, 1, 1, 1, 1,  # arms
    1, 1, 1, 1, 1, 1, 1   # arms 
]

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


class Mode:
    PR = 0  # Series Control for Pitch/Roll Joints
    AB = 1  # Parallel Control for A/B Joints



class LowCMDControl_AllJoints:
    def __init__(self):
        self.time_ = 0.0
        self.t=0.0
        self.T=1.0
        self.control_dt_ = 0.002  # [2ms]
        self.duration_ = 3.0    # [3 s]
        self.counter_ = 0
        self.target_pos = {}
        self.mode_pr_ = Mode.PR
        self.mode_machine_ = 0
        self.low_cmd = unitree_hg_msg_dds__LowCmd_()  
        self.low_state = None 
        self.update_mode_machine_ = False
        self.crc = CRC()

        # Single client for all operations
        self.client = None


    def Init(self):
        try:
            # Create and initialize LocoClient (single client for robot control)
            self.client = LocoClient()
            self.client.SetTimeout(10.0)
            self.client.Init()
            
            """
            # Initialize robot state
            
            print("Setting initial state...")
            self.client.Damp()
            time.sleep(INIT_DELAY)

            print("Standing up...")
            self.client.StandUp()
            time.sleep(STARTUP_DELAY)

            print("Starting robot...")
            self.client.Start()
            time.sleep(COMMAND_DELAY)
            """

            # Create publisher and subscriber
            self.lowcmd_publisher_ = ChannelPublisher("rt/lowcmd", LowCmd_)
            self.lowcmd_publisher_.Init()

            self.lowstate_subscriber = ChannelSubscriber("rt/lowstate", LowState_)
            self.lowstate_subscriber.Init(self.LowStateHandler, 10)

        except Exception as e:
            print(f"[ERROR] Failed during Init: {e}")
            raise

    def Start(self):
        self.lowCmdWriteThreadPtr = RecurrentThread(
            interval=self.control_dt_, target=self.LowCmdWrite, name="control"
        )
        while self.update_mode_machine_ == False:
            time.sleep(1)

        if self.update_mode_machine_ == True:
            self.lowCmdWriteThreadPtr.Start()
    
    

    def LowStateHandler(self, msg: LowState_):
        self.low_state = msg

        if self.update_mode_machine_ == False:
            self.mode_machine_ = self.low_state.mode_machine
            self.update_mode_machine_ = True
        
        self.counter_ +=1
        if (self.counter_ % 500 == 0) :
            self.counter_ = 0
            print(self.low_state.imu_state.rpy)

    def interpolate_position(self, q_init, q_target):
        ratio = (1 - math.cos(math.pi * (self.t / self.T))) / 2 if self.t < self.T else 1.0
        return q_init + (q_target - q_init) * ratio

    def LowCmdWrite(self):
        if self.low_state is None:
            return

        #self.low_cmd.motor_cmd[G1JointIndex.kNotUsedJoint].q = 1  # Enable arm_sdk

        for i in ARM_INDEXES:
            
            q_init = self.low_state.motor_state[i].q
            q_target = self.target_pos.get(i, q_init)
            pos = self.interpolate_position(q_init, q_target)

            self.low_cmd.mode_pr = Mode.PR
            self.low_cmd.mode_machine = self.mode_machine_
            self.low_cmd.motor_cmd[i].mode =  1 # 1:Enable, 0:Disable
            self.low_cmd.motor_cmd[i].mode = 1 
            self.low_cmd.motor_cmd[i].q = pos
            self.low_cmd.motor_cmd[i].dq = 0.0
            self.low_cmd.motor_cmd[i].tau = 0.0
            self.low_cmd.motor_cmd[i].kp = Kp[i]
            self.low_cmd.motor_cmd[i].kd = Kd[i]

        self.low_cmd.crc = self.crc.Crc(self.low_cmd)
        self.lowcmd_publisher_.Write(self.low_cmd)
        self.t += self.control_dt_





    def move_to(self, updates: dict, duration=5):
        self.target_pos.update(updates)
        self.T = duration
        self.t = 0.0

        while self.t < self.T:
            time.sleep(self.control_dt_)


    def getch(self):
        """
        Get a single character from the user without requiring Enter key.
        Returns:
            str: Single character input from the user
        """
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def print_controls(self):
        """Display available control commands to the user."""
        print("\nUnitree G1 Robot Controls:")
        print("-------------------------")
        print("Movement:")
        print("  W: Move Forward")
        print("  S: Move Backward")
        print("  A: Move Left")
        print("  D: Move Right")
        print("  Q: Rotate Left")
        print("  E: Rotate Right")
        print("  M: Move Arms")
        print("\nOther Commands:")
        print("  Space: Stop")
        print("  Esc: Quit")
        print("\nCurrent Status: Robot Ready")


    def initialize_robot(self, network_interface):
        """
        Initialize the robot and get it ready for movement.
        Args:
            network_interface (str): Network interface to use for robot communication
        Returns:
            LocoClient: Initialized robot client
        """
        """
        ## Initialize SDK
        #ChannelFactoryInitialize(0, network_interface)
        
        # Create and initialize client
        client = LocoClient()
        client.SetTimeout(10.0)
        client.Init()
        
        # Initialize robot state
        print("Setting initial state...")
        client.Damp()
        time.sleep(INIT_DELAY)
        
        print("Standing up...")
        client.StandUp()
        time.sleep(STARTUP_DELAY)
        
        print("Starting robot...")
        client.Start()
        time.sleep(COMMAND_DELAY)
        """
        
        return self.client


    def handle_movement(self, key, client):
        """
        Handle movement commands based on key press.
        Args:
            key (str): The pressed key
            client (LocoClient): Robot client instance
        Returns:
            bool: True if should continue, False if should exit
        """
        x_vel = 0.0
        y_vel = 0.0
        yaw_vel = 0.0
        status = "Stopped          "

        if key == 'w':
            x_vel = FORWARD_SPEED
            status = "Moving Forward    "
        elif key == 's':
            x_vel = -FORWARD_SPEED
            status = "Moving Backward   "
        elif key == 'a':
            y_vel = LATERAL_SPEED
            status = "Moving Left       "
        elif key == 'd':
            y_vel = -LATERAL_SPEED
            status = "Moving Right      "
        elif key == 'q':
            yaw_vel = ROTATION_SPEED
            status = "Rotating Left     "
        elif key == 'e':
            yaw_vel = -ROTATION_SPEED
            status = "Rotating Right    "
        elif key == ' ':
            status = "Stopped          "
        elif ord(key) == 27:  # Esc key
            print("\nExiting...")
            return False
        
        if key == 'm':
            self.target_pos.update(POSICION1)
        elif key == 'n':
            self.target_pos.update(POSICION2)

        print(f"\rCurrent Status: {status}", end='')
        client.Move(x_vel, y_vel, yaw_vel)
        sys.stdout.flush()
        return True


def main():
    """Main function to run the robot control program."""
    if len(sys.argv) < 2:
        sys.exit("Uso: python3 lowcmd_alljoints.py <interfaz_red>")

    print("\nWARNING: Please ensure there are no obstacles around the robot.")
    input("Press Enter when the area is clear...")

    if len(sys.argv)>1:
        ChannelFactoryInitialize(0, sys.argv[1])
    else:
        ChannelFactoryInitialize(0)

    seq = LowCMDControl_AllJoints()
    try:
        seq.Init()
    except Exception as e:
        print("Failed to initialize joint controller. Exiting.")
        return
    seq.Start()

    
    client = None  # <-- Fix: declare client before the try block

    try:
        # Initialize robot
        client = seq.initialize_robot(sys.argv[1])
        seq.print_controls()

        # Main control loop
        while True:
            key = seq.getch().lower()
            if not seq.handle_movement(key, client):
                break

    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
    finally:
        # Ensure robot stops safely
        try:
            client.Move(0, 0, 0)
            print("\nRobot stopped safely")
        except Exception as e:
            print(f"\nError stopping robot: {str(e)}")


if __name__ == "__main__":
    main()
