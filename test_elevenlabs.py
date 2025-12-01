import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

print(f"Testing API Key: {API_KEY[:5]}...{API_KEY[-5:] if API_KEY else 'None'}")

url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
headers = {
    "xi-api-key": API_KEY,
    "Content-Type": "application/json"
}
data = {
    "text": "Hello, this is a test.",
    "model_id": "eleven_monolingual_v1",
    "voice_settings": {
        "stability": 0.5,
        "similarity_boost": 0.75
    }
}

print("\nAttempting to generate audio...")
response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    print("\n[OK] TTS Generation SUCCESSFUL!")
    print(f"Received {len(response.content)} bytes of audio.")
    print("Your API key works for speaking!")
else:
    print(f"\n[ERROR] TTS Failed: {response.status_code}")
    print(f"Message: {response.text}")
