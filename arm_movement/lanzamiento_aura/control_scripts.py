import os
import sys
import time
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient

def listar_scripts(directorio):
    scripts = []
    for archivo in sorted(os.listdir(directorio)):
        if archivo.endswith(".py") and not archivo.startswith("release"):
            scripts.append(archivo)
    return scripts

def ejecutar_script(ruta_script, interfaz):
    os.system(f"python3 {ruta_script} {interfaz}")

def menu_categoria(nombre, path_categoria, interfaz):
    while True:
        print(f"\n--- {nombre.upper()} ---")
        scripts = listar_scripts(path_categoria)
        for i, script in enumerate(scripts):
            print(f"  {i+1}. {script}")
        print("  B. Volver al menú principal")
        print("  R. Release control de los brazos")

        eleccion = input("Selecciona una opción: ").strip().lower()

        if eleccion == 'b':
            break
        elif eleccion == 'r':
            ejecutar_script(os.path.join(path_categoria, "../release_arm_sdk.py"), interfaz)
        elif eleccion.isdigit() and 1 <= int(eleccion) <= len(scripts):
            ejecutar_script(os.path.join(path_categoria, scripts[int(eleccion)-1]), interfaz)
        else:
            print("Opción no válida.")

def menu_principal(interfaz):
    base_path = "lanzamiento_aura"
    categorias = {
        '1': ("Gestos", os.path.join(base_path, "gestos")),
        '2': ("Bailes", os.path.join(base_path, "bailes")),
        '3': ("Coordinación", os.path.join(base_path, "coordinacion")),
        '4': ("Entrevista", os.path.join(base_path, "entrevista")),
        '5': ("Poses", os.path.join(base_path, "poses")),
    }

    while True:
        print("\n--- MENÚ PRINCIPAL ---")
        for key, (nombre, _) in categorias.items():
            print(f"  {key}. {nombre}")
        print("  R. Release control de los brazos")
        print("  S. Salir")

        opcion = input("Selecciona una categoría: ").strip().lower()

        if opcion == 's':
            break
        elif opcion == 'r':
            ejecutar_script(os.path.join(base_path, "release_arm_sdk.py"), interfaz)
        elif opcion in categorias:
            nombre, path = categorias[opcion]
            menu_categoria(nombre, path, interfaz)
        else:
            print("Opción no válida.")

def inicializar_robot(interfaz):
    print("Inicializando comunicación con el robot...")
    ChannelFactoryInitialize(0, interfaz)
    client = LocoClient()
    client.SetTimeout(10.0)
    client.Init()
    return client

def main():
    if len(sys.argv) < 2:
        print(f"Uso: python3 {sys.argv[0]} <interfaz_red>")
        sys.exit(1)

    interfaz = sys.argv[1]

    print("Asegúrese de que el área esté despejada.")
    input("Presiona Enter para continuar...")

    ya_inicializado = input("¿El robot ya está en modo [Main Operation Control] (equilibrio activado)? [s/n]: ").strip().lower()

    if ya_inicializado == 's':
        ChannelFactoryInitialize(0, interfaz)
        client = LocoClient()
        client.SetTimeout(10.0)
        client.Init()
        print("Robot conectado. Control disponible.")
    elif ya_inicializado == 'n':
        client = inicializar_robot(interfaz)
        print("Ejecutando rutina de inicio completa...")
        input('Presione Enter para entrar en modo [Damping mode] (L1+A)')
        client.Damp()
        time.sleep(1.0)

        input('Presione Enter para entrar en modo [Get Ready] (L1+UP)')
        client.StandUp()
        time.sleep(5.0)

        input('Presione Enter para activar el control de equilibrio [Main Operation Control] (R2+X)')
        client.BalanceStand(0)
        time.sleep(2.0)

        client.Start()
        time.sleep(2.0)
        print("Robot en modo operativo principal.")
    else:
        print("Opción no válida. Saliendo...")
        return

    menu_principal(interfaz)

if __name__ == "__main__":
    main()