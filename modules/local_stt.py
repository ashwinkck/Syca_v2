"""
Local Speech-to-Text using OpenAI Whisper
Fast, accurate, and runs entirely offline
"""

import whisper
import numpy as np
import sounddevice as sd
import soundfile as sf
import tempfile
import os
import sys
from pathlib import Path

# Add parent directory to path for config import
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import Config


class LocalSTT:
    """Local speech-to-text using Whisper"""
    
    def __init__(self, model_name=None, device=None):
        """
        Initialize Whisper model
        
        Args:
            model_name: tiny, base, small, medium, large (default from config)
            device: cpu or cuda (default from config)
        """
        self.model_name = model_name or Config.WHISPER_MODEL
        self.device = device or Config.WHISPER_DEVICE
        
        print(f"[STT] Loading Whisper model '{self.model_name}' on {self.device}...")
        
        try:
            self.model = whisper.load_model(self.model_name, device=self.device)
            print(f"[OK] Whisper ready ({self.model_name})")
        except Exception as e:
            print(f"[ERROR] Failed to load Whisper: {e}")
            raise
    
    def transcribe_file(self, audio_path, language="en"):
        """
        Transcribe audio file to text
        
        Args:
            audio_path: Path to audio file
            language: Language code (default: en)
            
        Returns:
            str: Transcribed text
        """
        try:
            result = self.model.transcribe(
                audio_path,
                language=language,
                fp16=False  # Use fp32 for CPU compatibility
            )
            return result["text"].strip()
        except Exception as e:
            print(f"[ERROR] Transcription error: {e}")
            return None
    
    def transcribe_numpy(self, audio_data, sample_rate=16000, language="en"):
        """
        Transcribe numpy array directly
        
        Args:
            audio_data: numpy array of audio samples
            sample_rate: Sample rate (default: 16000)
            language: Language code
            
        Returns:
            str: Transcribed text
        """
        try:
            # Whisper expects float32 in range [-1, 1]
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32768.0
            
            # Resample to 16kHz if needed (Whisper requirement)
            if sample_rate != 16000:
                # Simple resampling (for production, use librosa.resample)
                audio_data = self._resample(audio_data, sample_rate, 16000)
            
            # Transcribe
            result = self.model.transcribe(
                audio_data, 
                language=language,
                fp16=False,
                initial_prompt=f"Hello, my name is {Config.ROBOT_NAME}. I am a robot assistant."
            )
            return result["text"].strip()
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return None
    
    def _resample(self, audio, orig_sr, target_sr):
        """Simple resampling (basic implementation)"""
        duration = len(audio) / orig_sr
        target_length = int(duration * target_sr)
        indices = np.linspace(0, len(audio) - 1, target_length)
        return np.interp(indices, np.arange(len(audio)), audio)
    
    def record_and_transcribe(self, duration=5, language="en"):
        """
        Record audio from microphone and transcribe
        
        Args:
            duration: Recording duration in seconds
            language: Language code
            
        Returns:
            str: Transcribed text
        """
        print(f"[STT] Recording for {duration} seconds...")
        
        try:
            # Record audio
            sample_rate = 16000
            audio_data = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype=np.float32
            )
            sd.wait()
            
            print("[STT] Transcribing...")
            
            # Transcribe
            text = self.transcribe_numpy(audio_data.flatten(), sample_rate, language)
            
            if text:
                print(f"[OK] Recognized: {text}")
            else:
                print("[WARN] No speech detected")
            
            return text
            
        except Exception as e:
            print(f"[ERROR] Recording error: {e}")
            return None
    
    def get_model_info(self):
        """Get model information"""
        return {
            "model": self.model_name,
            "device": self.device,
            "languages": whisper.tokenizer.LANGUAGES
        }
