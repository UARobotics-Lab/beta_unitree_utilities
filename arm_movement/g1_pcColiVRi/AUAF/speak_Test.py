# from gtts import gTTS
# import os

# text = "Hola, ¿Como estas?"
# speech = gTTS(text=text, lang='es', slow=False)
# speech.save("output.mp3")
# os.system("start output.mp3")

from gtts import gTTS
from playsound import playsound
import os
import tempfile

def speak_text(text, lang='es'):
    """Converts text to speech and plays it."""

    tts = gTTS(text=text, lang=lang)
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmpfile:
        tts.save(tmpfile.name)
        temp_filename = tmpfile.name
    
    try:
        playsound(temp_filename)
    except Exception as e:
            print(f"Error playing sound: {e}")
    finally:
        os.remove(temp_filename) # Remove the temporary file

# Example usage
speak_text("Hello, this is a test message.")
speak_text("Hola, esto es un mensaje de prueba.", lang="es")