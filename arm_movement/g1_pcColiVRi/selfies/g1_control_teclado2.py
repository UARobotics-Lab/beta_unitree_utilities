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
        print("  r       → Liberar control de los brazos")
        print("  P       → Parada directa: entra en modo DAMP y cierra el programa")
        print('  1       → ShakeHand (Dar la mano) OG')
        print('  2       → WaveHand (Saludo) OG')
        print('  3       → TurnedWaveHand (Saludo invertido) OG')
        print('  4       → Alvaro')
        print('  5       → Samuel')
        print('  6       → Juan David')
        print('  7       → Jhon')
        print('  8       → David')
        print('  9       → Nicolas')

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
    print("¿El robot se encuentra ya con el equilibrio encendido (Main Operation Control) [s/n]?")

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
            elif key == 'r':
                print("Liberando control de los brazos...")
                import subprocess
                subprocess.Popen(["python3", "release_arm_sdk.py", sys.argv[1]])
                print("Control de los brazos liberado.")
                info_controles()
            elif key == '1':
                print("ShakeHand (Dar la mano)")
                client.ShakeHand()
                info_controles()
            elif key == '2':
                print("Ejecutando WaveHand (Saludo)...")
                client.WaveHand()
                print("WaveHand (Saludo) finalizado.")
                info_controles()
            elif key == '3':
                print("Ejecutando TurnedWaveHand (Saludo invertido)...")
                client.WaveHand()
                print('TurnedWaveHand (Saludo invertido) finalizado.')
                info_controles()
            elif key == '4':
                print("Ejecutando...")
                import subprocess
                subprocess.Popen(["python3", "alvaro.py", sys.argv[1]])
                print("Ejecucion finalizada.")
                info_controles()
            elif key == '5':
                print("Ejecutando...")
                import subprocess
                subprocess.Popen(["python3", "samuel.py", sys.argv[1]])
                print("Ejecucion finalizada.")
                info_controles()
            elif key == '6':
                print("Ejecutando...")
                import subprocess
                subprocess.Popen(["python3", "juandavid.py", sys.argv[1]])
                print("Ejecucion finalizada.")
                info_controles()
            elif key == '7':
                print("Ejecutando...")
                import subprocess
                subprocess.Popen(["python3", "jhon.py", sys.argv[1]])
                print("Ejecucion finalizada.")
                info_controles()
            elif key == '8':
                print("Ejecutando...")
                import subprocess
                subprocess.Popen(["python3", "david.py", sys.argv[1]])
                print("Ejecucion finalizada.")
                info_controles()
            elif key == '9':
                print("Ejecutando...")
                import subprocess
                subprocess.Popen(["python3", "nicolas.py", sys.argv[1]])
                print("Ejecucion finalizada.")
                info_controles()
            elif key == 'p':
                client.Damp()
                print("Se activo la parada de emergencia (tecla 'p').")
                print("Robot en [Damping Mode]. Terminando ejecucion, oprima [ctr+c]...")
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
                client.Sit()
                print("Robot sentado.")
                break
            else:
                print("Opcion no valida. Intenta de nuevo.")

        print("Programa finalizado.")

if __name__ == "__main__":
    main()