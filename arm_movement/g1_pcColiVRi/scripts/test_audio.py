from unitree_sdk2py.g1.audio.g1_audio_client import AudioClient
import sys
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
import wave
import numpy as np
import os
from scipy.io import wavfile
from scipy.signal import resample

PATH = os.path.abspath(os.path.dirname(__file__))

if __name__ == "__main__":
    ChannelFactoryInitialize(0, sys.argv[1])
    client = AudioClient()
    client.Init()

    sample_rate, data = wavfile.read(f"{PATH}/test.wav")
    maxval = np.iinfo(data.dtype).max
    data = (data.astype(np.float32) / (maxval + 1)) * 127.5
    data = np.clip(data, 0, 255).astype(np.uint8)

    print(sample_rate, data.dtype)

    client.SetVolume(70)
    client.StartPlay("example", bytearray(data))