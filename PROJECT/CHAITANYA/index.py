import threading
import queue
import time
import requests
import speech_recognition as sr
import pyttsx3
import webbrowser

# Your GitHub token (ensure you secure this for production)
GITHUB_TOKEN = "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"

# Initialize the text-to-speech engine
engine = pyttsx3.init()

# A thread-safe queue for recognized voice commands
command_queue = queue.Queue()

def speak(text):
    """
    Speak the provided text asynchronously.
    Only speaks responses coming from the GitHub API.
    """
    def run_speech():
        engine.say(text)
        engine.runAndWait()
    threading.Thread(target=run_speech, daemon=True).start()
    print("AI Assistant:", text)

def background_callback(recognizer, audio):
    """
    Callback for background listening.
    Converts spoken audio to text, stops any ongoing TTS,
    and puts the command into a queue.
    """
    try:
        command = recognizer.recognize_google(audio).lower()
        engine.stop()  # Interrupt any ongoing speech
        command_queue.put(command)
    except Exception:
        # Ignore errors silently
        pass

def search_github(query):
    """
    Search GitHub for repositories matching the query.
    Speaks only the repository names returned by the API.
    """
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    url = "https://api.github.com/search/repositories"
    params = {"q": query}
    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            results = response.json()
            items = results.get("items", [])
            if items:
                # Speak the full names of the first 5 repositories (if available)
                repo_names = ", ".join(repo.get("full_name", "unknown") for repo in items[:5])
                speak(repo_names)
            else:
                # No repositories found: remain silent
                speak("")
        else:
            # On API error, remain silent
            speak("")
    except Exception:
        # On exception, remain silent
        speak("")

def process_command(command):
    """
    Process the recognized command.
    Only commands matching our criteria are processed.
    Other commands are ignored (aside from logging for debugging).
    """
    # Exit command is always processed.
    if command.startswith("exit") or command.startswith("quit"):
        exit(0)
    # Process GitHub search command
    elif command.startswith("search github for"):
        query = command[len("search github for"):].strip()
        if query:
            search_github(query)
    # Process open website command
    elif command.startswith("open website"):
        url = command[len("open website"):].strip()
        if url:
            if not (url.startswith("http://") or url.startswith("https://")):
                url = "http://" + url
            webbrowser.open(url)
    # Process open YouTube command
    elif command.startswith("open youtube"):
        webbrowser.open("https://www.youtube.com")
    else:
        # For any other command, do nothing (but log for debugging)
        print("Unrecognized command (ignored):", command)

def main():
    # Greet the user once at startup.
    speak("Hi, my name is AI Assistant, what can I help you?")
    
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    # Calibrate the microphone for ambient noise.
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
    
    # Start background listening.
    stop_listening = recognizer.listen_in_background(microphone, background_callback)
    
    try:
        while True:
            try:
                # Process commands as they become available.
                command = command_queue.get(timeout=0.1)
                process_command(command)
            except queue.Empty:
                pass
            time.sleep(0.1)
    except KeyboardInterrupt:
        stop_listening(wait_for_stop=False)
        print("AI Assistant terminated.")

if __name__ == "__main__":
    main()
