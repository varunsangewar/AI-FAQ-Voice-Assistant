import pyttsx3

# You must import pythoncom to make speech work in background threads on Windows
# If you don't have it, install it in your terminal with: pip install pywin32
import pythoncom 

def speak(text):
    # 1. Tell Windows we are using COM in a background thread
    pythoncom.CoInitialize() 
    
    # 2. Initialize the engine INSIDE the function, not at the top of the file
    engine = pyttsx3.init()
    
    # 3. Speak the text
    engine.say(text)
    engine.runAndWait()