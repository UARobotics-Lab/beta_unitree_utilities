"""
Control del robot Unitree G1 usando teclado (WASD)
"""
import os
import sys
import time
import tty
import termios
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient

# Constantes de velocidad
FORWARD_SPEED = 0.3
LATERAL_SPEED = 0.3
ROTATION_SPEED = 0.3

# Delays
INIT_DELAY = 1.0
STARTUP_DELAY = 5.0
COMMAND_DELAY = 2.0

def getch():
    """Captura una tecla sin requerir Enter."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def info_controles ():
        print("\nAYUDA - Controles disponibles:")
        print("  W/A/S/D → Moverse")
        print("  Q/E     → Rotar")
        print("  ESPACIO → Detenerse sin apagar")
        print("  ESC     → Salir con opciones de apagado")
        print("  P       → Parada directa: entra en modo DAMP y cierra el programa")
        print('  1       → Posicion inicial de los brazos')
        print('  2       → Ubicacion de brazos para levantar caja')
        print('  3       → Levantar caja')
        print('  4       → Soltar caja')

def initialize_robot(net_interface):
    """Inicializa el robot y lo deja listo para caminar."""
    print("Inicializando comunicacion con el robot...")
    ChannelFactoryInitialize(0, net_interface)
    
    client = LocoClient()
    client.SetTimeout(10.0)
    client.Init()

    print('Robot en modo [Zero Torque]')
    input('Presiones Enter para entrar en [Damping mode] (L1+A)')
    print("Damping mode...")
    client.Damp()
    time.sleep(INIT_DELAY)
    print('Estado actual: [Damping mode]')

    input('Presione Enter para entrar en modo [Get Ready] (L1+UP)')
    print("Get Ready...")
    client.StandUp()
    time.sleep(STARTUP_DELAY)
    print('Estado actual: Get Ready')
    print('Descuelgue el robot para que este apoyado con algo de flexion en las rodillas antes del activar el control de equilibrio...')

    input('Presiones Enter para activar el control de equilibrio [Main Operation Control] (R2+X)')
    print("Activando modo control de equilibrio...")
    client.BalanceStand(0)
    time.sleep(2.0)
    print("Iniciando robot...")
    client.Start()
    time.sleep(COMMAND_DELAY)
    print('Estado actual: Main Operation Control')
    print('Utilice el control oprimiendo (R1+X) y poner el robot en modo caminata')

    return client

def main():
    if len(sys.argv) < 2:
        print(f"Uso: python3 {sys.argv[0]} <interfaz_red>")
        sys.exit(1)

    print("Asegurese de que el area este despejada.")
    input("Presiona Enter para continuar...")

    client = initialize_robot(sys.argv[1])
    
    info_controles()

    try:
        while True:
            key = getch().lower()
            x, y, yaw = 0.0, 0.0, 0.0

            if key == 'w':
                x = FORWARD_SPEED
            elif key == 's':
                x = -FORWARD_SPEED
            elif key == 'a':
                y = LATERAL_SPEED
            elif key == 'd':
                y = -LATERAL_SPEED
            elif key == 'q':
                yaw = ROTATION_SPEED
            elif key == 'e':
                yaw = -ROTATION_SPEED
            elif key == '1':
                print("Llevanto brazos a posicion de inicializacion")
                import subprocess
                subprocess.Popen(["python3", "init_arms.py", sys.argv[1]])
            elif key == '2':
                print("Ubicando brazos. Acerque a Unitree G1 a la caja...")
                import subprocess
                subprocess.Popen(["python3", "ubicar_agarrar.py", sys.argv[1]])
            elif key == '3':
                print("Levantando caja. Unitree G1 listo para deplazar la caja...")
                import subprocess
                subprocess.Popen(["python3", "agarrar_desplazamiento.py", sys.argv[1]])
            elif key == '4':
                print("Soltando caja. Retire a Unitree G1 de la zona de carga...")
                import subprocess
                subprocess.Popen(["python3", "ubicar_soltar.py", sys.argv[1]])
            elif key == 'p':
                client.Damp()
                print("Se activo la parada de emergencia (tecla 'p').")
                print("Robot en [Damping Mode]. Terminando ejecucion inmediata...")
                os.exit(0)
            elif key == 'h':
                info_controles()
            elif key == ' ':
                x = y = yaw = 0.0
            elif ord(key) == 27:
                print("\nSaliendo del programa...")
                break
            client.Move(x, y, yaw)
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario.")
    finally:
        print("Deteniendo el robot...")
        client.Move(0, 0, 0)
        time.sleep(0.5)

        print("Selecciona una acción de apagado:")
        print("  1 - Modo seguro (Damp/L1+A)")
        print("  2 - Sentarse (SitDown/REVISAKBRON)")
        
        while True:
            opcion = input("Escribe 1 o 2 y presiona Enter: ").strip()
            if opcion == '1':
                input("Presiona Enter para entrar en [Damping mode/L1+A]...")
                client.Damp()
                print("Robot en modo Damp.")
                break
            elif opcion == '2':
                input("Presiona Enter para que el robot se siente...")
                client.Damp()
                print("Robot sentado.")
                break
            else:
                print("Opcion no valida. Intenta de nuevo.")

        print("Programa finalizado.")

if __name__ == "__main__":
    main()