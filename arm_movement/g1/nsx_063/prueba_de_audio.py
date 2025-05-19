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

    '''Establecimiento de volumen'''
    ret = audio_client.GetVolume()
    print("Volumen actual:", ret)

    def solicitar_volumen():
        while True:
            vol_input = input(f"Ingrese volumen deseado [1,100] o presione Enter para mantener el actual [{ret}]: ")

            if vol_input.strip() == "":
                return ret  # Usa el volumen actual si no se ingresó nada

            try:
                vol = int(vol_input)
                if 1 <= vol <= 100:
                    return vol
                else:
                    print("El numero debe estar entre 1 y 100.")
            except ValueError:
                print("Entrada invalida. Solo se aceptan numeros enteros.")

    volumen = solicitar_volumen()
    audio_client.SetVolume(volumen)
    print("Volumen configurado a:", volumen)


    sport_client.WaveHand() #Hace que el robot levante la mano y salude
    
    '''Pruebas de voz'''
    input("Presione ENTER para comenzar la prueba de voz en chino...")
    print('Ejecutando prueba de voz en chino del fabricante...')
    audio_client.TtsMaker("大家好!我是宇树科技人形机器人。语音开发测试例程运行成功！ 很高兴认识你！", 0)
    print('Traduccion: ¡Hola a todos! Soy el robot humanoide de Unitree Robotics. ¡El ejemplo de prueba de desarrollo de voz se ejecuto con exito! ¡Encantado de conocerte!')
    time.sleep(8)
    
    input("Presione ENTER para probar voces en español (cambiando speaker_id)...")
    for i in range(10):
        input(f"Presione ENTER para probar speaker_id {i}...")
        print(f"Reproduciendo voz con speaker_id: {i}")
        audio_client.TtsMaker("Probando, probando, uno, dos, tres, uno!, ¡uno!, diferentes voces en espaniol, español, ¡español!", i)
        time.sleep(3)

    # Final
    input('Presione ENTER para finalizar la prueba de voz...')
    print('Pruebas de habla finalizadas...')
    time.sleep(3)
    audio_client.TtsMaker("测试完毕，谢谢大家！", 0)
    print('Traduccion: Prueba finalizada, ¡gracias a todos!')
    


    
