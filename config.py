import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Hybrid configuration for local + cloud processing"""
    
    # ============================================
    # ROBOT IDENTITY
    # ============================================
    # ROBOT_NAME = os.getenv("ROBOT_NAME", "Ava")
    ROBOT_NAME = "Ava"  # Forced name change
    
    # ============================================
    # PROCESSING MODE
    # ============================================
    # Options: "speed" (all local), "quality" (prefer cloud), "balanced" (smart routing)
    MODE = os.getenv("MODE", "balanced")
    USE_CLOUD_FALLBACK = os.getenv("USE_CLOUD_FALLBACK", "true").lower() == "true"
    
    # ============================================
    # LOCAL MODELS (Primary - Fast & Free)
    # ============================================
    
    # Ollama (Local LLM)
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2")
    OLLAMA_VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "llava")
    
    # Whisper (Local STT)
    # Options: tiny, base, small, medium, large
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
    WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")  # or "cuda" for GPU
    
    # Coqui TTS (Local TTS)
    TTS_MODEL = os.getenv("TTS_MODEL", "tts_models/en/ljspeech/tacotron2-DDC")
    TTS_USE_GPU = os.getenv("TTS_USE_GPU", "false").lower() == "true"
    
    # ============================================
    # CLOUD FALLBACK (Optional - High Quality)
    # ============================================
    
    # OpenRouter
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    CLOUD_CHAT_MODEL = os.getenv("CLOUD_CHAT_MODEL", "nvidia/nemotron-nano-12b-v2-vl:free")
    CLOUD_VISION_MODEL = os.getenv("CLOUD_VISION_MODEL", "nvidia/nemotron-nano-12b-v2-vl:free")
    
    # ElevenLabs
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    ELEVENLABS_MODEL = "eleven_monolingual_v1"
    ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech"
    
    # ============================================
    # PERFORMANCE TUNING
    # ============================================
    
    # Vision
    VISION_CACHE_SECONDS = 10  # Cache vision analysis
    VISION_ANALYSIS_INTERVAL = 5  # Seconds between auto-analysis
    
    # Response timeouts
    LOCAL_TIMEOUT = 60  # Seconds before falling back to cloud (Increased for stability)
    CLOUD_TIMEOUT = 30  # Seconds before giving up
    
    # Streaming
    ENABLE_TTS_STREAMING = True  # Start playing audio before full generation
    ENABLE_RESPONSE_CHUNKING = True  # Stream responses word-by-word
    
    # Storage
    MAX_AUDIO_FILES = 5  # Keep only the last N audio files to save space
    
    # ============================================
    # MEDIA DIRECTORIES
    # ============================================
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MEDIA_DIR = os.path.join(BASE_DIR, "media")
    AUDIO_DIR = os.path.join(MEDIA_DIR, "audio")
    IMAGE_DIR = os.path.join(MEDIA_DIR, "images")
    
    # Create directories
    os.makedirs(AUDIO_DIR, exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)
    
    # ============================================
    # VALIDATION
    # ============================================
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        print("\n" + "="*60)
        print(f"  [{cls.ROBOT_NAME}] v2 - Hybrid Configuration")
        print("="*60)
        
        # Check local models
        print("\n[LOCAL] Local Models:")
        print(f"  • Ollama: {cls.OLLAMA_HOST}")
        print(f"    - Chat: {cls.OLLAMA_CHAT_MODEL}")
        print(f"    - Vision: {cls.OLLAMA_VISION_MODEL}")
        print(f"  • Whisper: {cls.WHISPER_MODEL} ({cls.WHISPER_DEVICE})")
        print(f"  • TTS: {cls.TTS_MODEL}")
        
        # Check cloud fallback
        print(f"\n[CLOUD] Cloud Fallback: {'Enabled' if cls.USE_CLOUD_FALLBACK else 'Disabled'}")
        if cls.USE_CLOUD_FALLBACK:
            has_openrouter = bool(cls.OPENROUTER_API_KEY)
            has_elevenlabs = bool(cls.ELEVENLABS_API_KEY)
            print(f"  - OpenRouter: {'[OK]' if has_openrouter else '[NO] (missing key)'}")
            print(f"  - ElevenLabs: {'[OK]' if has_elevenlabs else '[NO] (missing key)'}")
        
        # Mode
        print(f"\n[MODE] Mode: {cls.MODE.upper()}")
        
        print("\n" + "="*60 + "\n")
        
        return True
    
    @classmethod
    def get_system_prompt(cls):
        """Get robot system prompt"""
        return f"""CRITICAL INSTRUCTION: You are {cls.ROBOT_NAME}, a real physical robot.
        
RULES:
1. BE CONCISE: Keep answers short (1-2 sentences).
2. NO ACTING: Do not use asterisks (*smiles*) or describe actions.
3. NO MARKDOWN: Do not use bold (**text**) or italics. Write plain text only.
4. NO HALLUCINATIONS: You are NOT 'Niles' or 'Nemotron'. You are {cls.ROBOT_NAME}.
5. NATURAL SPEECH: Write exactly what should be spoken. No emojis.

Context: You have a camera and can see the user.
"""


if __name__ == "__main__":
    Config.validate()
