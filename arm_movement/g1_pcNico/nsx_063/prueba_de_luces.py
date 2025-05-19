import time
import sys
from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize #Inicializa la comunicacion con el robot
from unitree_sdk2py.g1.audio.g1_audio_client import AudioClient #Para utilizar las funciones de voz, volumen y luces
from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient #Para poder hacer control de movimiento

if __name__ == "__main__":
    '''Verificacion de la interfaz de red'''
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} networkInterface")
        sys.exit(-1)

    '''Inicializa la conexión del SDK con el robot a través de la interfaz de red'''
    ChannelFactoryInitialize(0, sys.argv[1])

    '''Crea la instancia de AudioClient'''
    audio_client = AudioClient()  
    audio_client.SetTimeout(10.0)
    audio_client.Init()

    '''Crea la instancia de de LocoClient'''
    sport_client = LocoClient()  
    sport_client.SetTimeout(10.0)
    sport_client.Init()
    
    sport_client = LocoClient()  
    sport_client.SetTimeout(10.0)
    sport_client.Init()

    '''Control de volumen'''
    ret = audio_client.GetVolume()
    print("Volumen actual: ",ret) #Obtiene el volumen actual y lo imprime

    audio_client.SetVolume(85) #Establece el volumen a 85 para la prueba

    ret = audio_client.GetVolume()
    print("Volumen establecido: ",ret) #Imprime el nuevo volumen establecido

    
    '''Pruebas de luces'''
    input("Presione ENTER para comenzar la prueba de luces LED del fabricante...")
    audio_client.TtsMaker("接下来测试灯带开发例程！", 0)
    print('Traduccion: A continuacion, se probara el ejemplo de desarrollo de la tira de luces.')
    time.sleep(1)

    # Control de luces: prueba fabricante
    audio_client.LedControl(255, 0, 0)
    time.sleep(1)
    audio_client.LedControl(0, 255, 0)
    time.sleep(1)
    audio_client.LedControl(0, 0, 255)
    print('Prueba de luces del fabricante terminada...')

    input("Presione ENTER para comenzar la prueba de luces LED modo Rainbow...")
    print('Comenzando prueba...')
    input("Presione ENTER para establecer las luces LED en color ROJO...")
    audio_client.LedControl(255, 0, 0)  # Rojo
    print('Luces LED establecidas en color ROJO...')
    time.sleep(5)
    input("Presione ENTER para establecer las luces LED en color VERDE...")
    audio_client.LedControl(0, 255, 0)  # Verde
    print('Luces LED establecidas en color VERDE...')
    time.sleep(5)
    input("Presione ENTER para establecer las luces LED en color AZUL...")
    audio_client.LedControl(0, 0, 255)  # Azul
    print('Luces LED establecidas en color AZUL...')
    time.sleep(5)
    input("Presione ENTER para establecer las luces LED en color AMARILLO...")
    audio_client.LedControl(255, 255, 0)  # Amarillo (rojo + verde)
    print('Luces LED establecidas en color AMARILLO...')
    time.sleep(5)
    input("Presione ENTER para establecer las luces LED en color BLANCO...")
    audio_client.LedControl(255, 255, 255)  # Blanco (todos los colores al máximo)
    print('Luces LED establecidas en color BLANCO...')
    time.sleep(5)
    input("Presione ENTER para establecer las luces en estado apagado...")
    audio_client.LedControl(0, 0, 0)  # Apagar LEDs
    print('Luces LED establecidas para estado apagado...')
    time.sleep(5)
    print('Prueba de luces Rainbow finalizda...')

    input("Presione ENTER para comenzar la prueba de luces LED personalizadas...")
    def solicitar_color_rgb():
        print("\nControl de LEDs RGB")
        print("Ingrese los valores para cada componente de color:")
        print("Rojo, Verde, Azul — cada uno debe estar entre 0 y 255.")

        def pedir_componente(nombre):
            while True:
                try:
                    valor = int(input(f"Ingrese valor para {nombre} [0,255]: "))
                    if 0 <= valor <= 255:
                        return valor
                    else:
                        print(f"El valor de {nombre} debe estar entre 0 y 255.")
                except ValueError:
                    print(f"Entrada invalida para {nombre}. Solo se aceptan numeros enteros.")

        R = pedir_componente("Rojo (R)")
        G = pedir_componente("Verde (G)")
        B = pedir_componente("Azul (B)")

        return R, G, B
    
    input("Presione ENTER para aplicar los colores personalizados a las luces LED...")
    R, G, B = solicitar_color_rgb()
    audio_client.LedControl(R, G, B)
    print(f"LED configurado con color RGB ({R}, {G}, {B})")
    print('Prueba de luces presonalizadas finalizda...')

    # Final
    input('Presione ENTER para finalizar la prueba de luces LED...')
    print('Pruebas de luces finalizadas...')
    time.sleep(3)
    audio_client.TtsMaker("测试完毕，谢谢大家！", 0)
    print('Traduccion: Prueba finalizada, ¡gracias a todos!')