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
        print("  R       → Liberar control de los brazos")
        print("  P       → Parada directa: entra en modo DAMP y cierra el programa")
        print('  1       → ShakeHand (Dar la mano) OG')
        print('  2       → WaveHand (Saludo) OG')
        print('  3       → TurnedWaveHand (Saludo invertido) OG')
        print('  4       → Saludo Entrada')
        print('  5       → Saludo Brazo Derecho')
        print('  6       → Abrazo')
        print('  7       → Gallina')
        print('  8       → Hi5')
        print('  9       → Sorprendido')
        print("  0       → ¡Oh no!")
        print("  M       → La Macarena")

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

    print("Asegúrese de que el área esté despejada.")
    input("Presiona Enter para continuar...")

    ya_inicializado = input("¿El robot ya está en modo [Main Operation Control] (equilibrio activado)? [s/n]: ").strip().lower()
    
    if ya_inicializado == 's':
        # Solo inicializar Aura sin hacer las rutinas de postura
        print("Saltando la rutina de inicialización completa...")
        ChannelFactoryInitialize(0, sys.argv[1])
        client = LocoClient()
        client.SetTimeout(10.0)
        client.Init()
        print("Aura conectada. Comenzando control...")
    elif ya_inicializado == 'n':
        client = initialize_robot(sys.argv[1])
    else:
        print('Opcion no valida. Intenta de nuevo...')
    
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
                subprocess.Popen(["python3", "entrada_saludo.py", sys.argv[1]])
                print("Ejecucion finalizada.")
                info_controles()
            elif key == '5':
                print("Ejecutando...")
                import subprocess
                subprocess.Popen(["python3", "saludoR.py", sys.argv[1]])
                print("Ejecucion finalizada.")
                info_controles()
            elif key == '6':
                print("Ejecutando...")
                import subprocess
                subprocess.Popen(["python3", "abrazo.py", sys.argv[1]])
                print("Ejecucion finalizada.")
                info_controles()
            elif key == '7':
                print("Ejecutando...")
                import subprocess
                subprocess.Popen(["python3", "gallina.py", sys.argv[1]])
                print("Ejecucion finalizada.")
                info_controles()
            elif key == '8':
                print("Ejecutando...")
                import subprocess
                subprocess.Popen(["python3", "hi5.py", sys.argv[1]])
                print("Ejecucion finalizada.")
                info_controles()
            elif key == '9':
                print("Ejecutando...")
                import subprocess
                subprocess.Popen(["python3", "sorprendido.py", sys.argv[1]])
                print("Ejecucion finalizada.")
                info_controles()
            elif key == '0':
                print("Ejecutando...")
                import subprocess
                subprocess.Popen(["python3", "ohno.py", sys.argv[1]])
                print("Ejecucion finalizada.")
                info_controles()
            elif key == 'm':
                print("Ejecutando...")
                import subprocess
                subprocess.Popen(["python3", "macarena.py", sys.argv[1]])
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

        while True:
            print("\nSelecciona una acción de apagado:")
            print("  1 - Modo seguro (Damp/L1+A)")
            print("  2 - Salir sin modificar estado actual del robot (quedarse de pie)")
            print("  3 - Sentarse (SitDown/REVISAKBRON)")

            opcion = input("Escribe 1, 2 o 3 y presiona Enter: ").strip()

            if opcion == '1':
                confirmar = input("¿Desea entrar en modo seguro (Damp)? [s/n]: ").strip().lower()
                if confirmar == 's':
                    input("Presiona Enter para ejecutar...")
                    client.Damp()
                    print("Robot en modo Damp.")
                    break
                else:
                    print("Acción cancelada. Volviendo al menú.")
            elif opcion == '2':
                confirmar = input("¿Desea salir sin modificar el estado actual del robot? [s/n]: ").strip().lower()
                if confirmar == 's':
                    input("Presiona Enter para ejecutar...")
                    print("Saliendo sin modificar el estado actual del robot.")
                    break
                else:
                    print("Acción cancelada. Volviendo al menú.")
            elif opcion == '3':
                confirmar = input("¿Desea que el robot se siente? [s/n]: ").strip().lower()
                if confirmar == 's':
                    input("Presiona Enter para ejecutar...")
                    client.Sit()
                    print("Robot sentado.")
                    break
                else:
                    print("Acción cancelada. Volviendo al menú.")
            else:
                print("Opción no válida. Intenta de nuevo.")

        print("Programa finalizado.")


if __name__ == "__main__":
    main()