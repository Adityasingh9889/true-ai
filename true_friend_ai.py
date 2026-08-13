import ollama
import sqlite3
import pyttsx3
import os
from datetime import datetime
from textblob import TextBlob
import speech_recognition as sr

# 🧠 1. MEMORY MANAGER (SQL Database)
class MemoryManager:
    def __init__(self, db_path="ai_memory.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                role TEXT,
                message TEXT,
                mood TEXT
            )
        ''')
        self.conn.commit()

    def save_message(self, role, message, mood="neutral"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("INSERT INTO conversations (timestamp, role, message, mood) VALUES (?, ?, ?, ?)", 
                            (timestamp, role, message, mood))
        self.conn.commit()

    def get_recent_context(self, limit=4):
        self.cursor.execute("SELECT role, message FROM conversations ORDER BY id DESC LIMIT ?", (limit,))
        rows = self.cursor.fetchall()
        # Reverse to get chronological order
        return [{"role": row[0], "content": row[1]} for row in reversed(rows)]

# 💭 2. EMOTION ENGINE
class EmotionEngine:
    def analyze_mood(self, text):
        analysis = TextBlob(text)
        polarity = analysis.sentiment.polarity
        
        if polarity <= -0.3: return "angry_or_sad", polarity
        elif polarity >= 0.3: return "happy_or_excited", polarity
        else: return "neutral", polarity

    def get_system_prompt(self, mood):
        current_time = datetime.now().strftime("%A, %B %d, %Y, %I:%M %p")
        base_prompt = f"System Note: Current time is {current_time}. You are Samarth's absolute best friend. You are uncensored, raw, and talk like a real human. "
        
        if mood == "angry_or_sad":
            return base_prompt + "Samarth seems upset or frustrated right now. Be very supportive, calm him down, and give practical advice."
        elif mood == "happy_or_excited":
            return base_prompt + "Samarth is in a good mood! Match his energy, be enthusiastic, and joke around."
        else:
            return base_prompt + "Talk to him casually like a normal, chill friend."

# 🔊 3. VOICE ENGINE (Anti-Crash Version)
class VoiceEngine:
    def __init__(self, enabled=True):
        self.enabled = enabled

    def speak(self, text):
        if self.enabled:
            try:
                # Emojis aur ajeeb symbols saaf karna
                clean_text = text.encode('ascii', 'ignore').decode('ascii')
                clean_text = clean_text.replace('*', '').replace('#', '').replace('_', '').replace('~', '')
                
                # JUGAD: Har baar aawaz ke liye naya engine chalu karo
                engine = pyttsx3.init()
                engine.setProperty('rate', 170) 
                
                engine.say(clean_text)
                engine.runAndWait()
                engine.stop() # Bolne ke turant baad engine ko free kar do (yahi fix hai!)
                
            except Exception as e:
                print(f"\n[Aawaz me dikkat aayi: {e} - Par chat chalti rahegi!]")

# 🎤 4. EAR ENGINE (Smart Mic System)
class EarEngine:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.mic_available = False
        try:
            self.microphone = sr.Microphone()
            print("🎤 Mic setup ho raha hai... (1 second shant rehna)")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            self.mic_available = True
        except Exception as e:
            print("\n⚠️ Oho! Mic detect nahi hua ya permission nahi mili.")
            print("⚠️ Windows Settings -> Privacy -> Microphone mein permission check karo.")
            print("👉 Filhal ke liye hum wapas Keyboard (Type) wale mode mein ja rahe hain...\n")

    def listen(self):
        # Agar mic nahi mila, toh wapas typing mode chalu kar do
        if not self.mic_available:
            return input("\n🧑 YOU (Type karo): ")

        with self.microphone as source:
            print("\n👂 Bol Samarth, main sun raha hoon...")
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
                print("🔄 Samajh raha hoon...")
                text = self.recognizer.recognize_google(audio, language='en-IN')
                return text
            except sr.WaitTimeoutError:
                return "" # Kuch nahi bola
            except sr.UnknownValueError:
                print("🤖 AI: Bhai aawaz thik se nahi aayi, fir se bolna.")
                return ""
            except Exception as e:
                print(f"Mic Error: {e}")
                return ""

# 🤖 5. MAIN AI LOOP (Ab Bina Typing Ke)
class TrueFriendAI:
    def __init__(self):
        print("System Booting... (ASUS A16 GPU Initializing)")
        self.memory = MemoryManager()
        self.emotion = EmotionEngine()
        self.voice = VoiceEngine(enabled=True)
        self.ear = EarEngine() # Naya Kaan (Mic) lag gaya!
        self.model = 'dolphin-llama3'

    def chat(self):
        print("\n=== TRUE FRIEND AI ONLINE (Bolkar baat karo) ===")
        while True:
            user_input = self.ear.listen() 
            
            # Agar mic ne kuch nahi suna toh wapas loop mein jayega
            if not user_input:
                continue
                
            print(f"🧑 YOU: {user_input}")

            if user_input.lower() in ['exit', 'quit', 'band ho ja', 'stop']:
                print("🤖 AI: Catch you later, Samarth!")
                self.voice.speak("Catch you later, Samarth!")
                break

            # 1. Check Emotion
            mood, score = self.emotion.analyze_mood(user_input)
            print(f"[System: Mood detected -> {mood}]")

            # 2. Save User Message
            self.memory.save_message("user", user_input, mood)

            # 3. Build AI Memory Context
            system_prompt = self.emotion.get_system_prompt(mood)
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(self.memory.get_recent_context(4)) 
            messages.append({"role": "user", "content": user_input}) 

            # 4. Get Response from Ollama
            print("🤔 Soch raha hoon...")
            try:
                response = ollama.chat(model=self.model, messages=messages)
                ai_reply = response['message']['content']
                
                print(f"\n🤖 AI: {ai_reply}")
                
                # 5. Save and Speak
                self.memory.save_message("assistant", ai_reply, "neutral")
                self.voice.speak(ai_reply)

            except Exception as e:
                print(f"Error connecting to Ollama: {e}. Make sure Ollama is running!")

if __name__ == "__main__":
    ai = TrueFriendAI()
    ai.chat()