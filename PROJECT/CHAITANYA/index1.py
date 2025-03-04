import speech_recognition as sr
import pyttsx3
import openai
import time

# Set your OpenAI API key
GITHUB_TOKEN = "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"

# Configure OpenAI API
openai.api_key = GITHUB_TOKEN
openai.api_base = "https://models.inference.ai.azure.com"
openai.api_type = "azure"
# If needed, specify API version
# openai.api_version = "2023-03-15-preview"

# Initialize text-to-speech engine
engine = pyttsx3.init()

def speak(text):
    """Speak the provided text using TTS."""
    engine.say(text)
    engine.runAndWait()

def listen_command():
    """Listen for a voice command and return the recognized text."""
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    with microphone as source:
        print("Listening for your command... (speak now)")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        command = recognizer.recognize_google(audio)
        print("You said:", command)
        return command.strip()
    except Exception as e:
        print("Error recognizing speech:", e)
        return ""

def ask_openai(query):
    """Process the user query using OpenAI API."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "my name is ai"},
                {"role": "user", "content": query},
            ],
            temperature=1,
            max_tokens=4096,
            top_p=1
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        print("Error communicating with OpenAI:", e)
        return "Sorry, I couldn't process that."

def main():
    print("AI Assistant is active. Say your command or 'exit' to quit.")
    speak("Hi, my name is AI. What can I help you with?")
    
    while True:
        user_query = listen_command().lower()
        if not user_query:
            print("No voice command detected, trying again...")
            time.sleep(0.5)
            continue

        if user_query in ["exit", "quit"]:
            speak("Goodbye!")
            break

        print("Processing your query...")
        answer = ask_openai(user_query)
        print("Response:", answer)
        speak(answer)
        print("Listening for your next command...")

if __name__ == "__main__":
    main()
