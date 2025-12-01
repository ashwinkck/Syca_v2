"""
Local Text-to-Speech using Coqui TTS
Fast, natural-sounding, and runs entirely offline
"""

import os
import sys
import re
import threading
import queue as queue_module
from pathlib import Path
from datetime import datetime
import numpy as np
import sounddevice as sd
import soundfile as sf
from TTS.api import TTS

# Add parent directory to path for config import
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import Config

try:
    from modules.cloud_fallback import CloudFallback
    CLOUD_AVAILABLE = True
except ImportError:
    CLOUD_AVAILABLE = False


class LocalTTS:
    """Local text-to-speech using Coqui TTS"""
    
    def __init__(self, model_name=None, use_gpu=None):
        """
        Initialize Coqui TTS
        
        Args:
            model_name: TTS model name (default from config)
            use_gpu: Use GPU if available (default from config)
        """
        self.model_name = model_name or Config.TTS_MODEL
        self.use_gpu = use_gpu if use_gpu is not None else Config.TTS_USE_GPU
        self.audio_dir = Config.AUDIO_DIR
        
        # Initialize Cloud Fallback for ElevenLabs
        self.cloud = None
        if CLOUD_AVAILABLE and Config.ELEVENLABS_API_KEY:
            try:
                self.cloud = CloudFallback()
                print("[TTS] ElevenLabs enabled (Primary)")
            except Exception as e:
                print(f"[WARN] ElevenLabs init failed: {e}")
        
        print(f"[TTS] Loading TTS model '{self.model_name}'...")
        
        try:
            self.tts = TTS(model_name=self.model_name, gpu=self.use_gpu)
            print(f"[OK] TTS ready ({self.model_name})")
        except Exception as e:
            print(f"[ERROR] Failed to load TTS: {e}")
            print("[TIP] Run 'tts --list_models' to see available models")
            raise
    
    def speak(self, text, save_file=True, play_audio=True):
        """
        Convert text to speech
        
        Args:
            text: Text to speak
            save_file: Save audio file (default: True)
            play_audio: Play audio immediately (default: True)
            
        Returns:
            str: Path to saved audio file (if save_file=True)
        """
        try:
            print(f"[TTS] Speaking: {text[:50]}...")
            
            # 1. Try ElevenLabs first (if configured)
            if self.cloud and Config.ELEVENLABS_API_KEY:
                try:
                    audio_path = self.cloud.speak_premium(text, save_file=save_file)
                    if audio_path:
                        if play_audio:
                            self._play_audio(audio_path)
                        return audio_path
                except Exception as e:
                    print(f"[WARN] ElevenLabs failed, falling back to local: {e}")
            
            # 2. Fallback to Local TTS
            # Generate audio file path
            if save_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                audio_path = os.path.join(self.audio_dir, f"tts_{timestamp}.wav")
            else:
                import tempfile
                audio_path = tempfile.mktemp(suffix=".wav")
            
            # Generate speech
            self.tts.tts_to_file(
                text=text,
                file_path=audio_path
            )
            
            # Play audio
            if play_audio:
                self._play_audio(audio_path)
            
            print(f"[OK] Audio {'saved and played' if play_audio else 'saved'}: {audio_path}")
            
            # Cleanup old files
            if save_file:
                self._cleanup_old_audio()
            
            return audio_path if save_file else None
            
        except Exception as e:
            print(f"[ERROR] TTS error: {e}")
            return None
    
    def speak_streaming(self, text, chunk_size=50):
        """
        Speak text in chunks for faster perceived response
        (Simulated streaming - generates full audio but plays in chunks)
        
        Args:
            text: Text to speak
            chunk_size: Characters per chunk
        """
        # Split text into sentences for more natural chunking
        sentences = self._split_sentences(text)
        
        for i, sentence in enumerate(sentences):
            print(f"[TTS] [{i+1}/{len(sentences)}] {sentence}")
            self.speak(sentence, save_file=False, play_audio=True)
    
    def _split_sentences(self, text):
        """Split text into sentences"""
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _play_audio(self, audio_path):
        """Play audio file"""
        try:
            # Read audio file
            data, sample_rate = sf.read(audio_path)
            
            # Play audio
            sd.play(data, sample_rate)
            sd.wait()  # Wait until audio finishes
            
        except Exception as e:
            print(f"[WARN] Playback error: {e}")
    
    def _cleanup_old_audio(self):
        """Delete old audio files, keeping only the most recent ones"""
        try:
            # Get all audio files
            audio_files = []
            for filename in os.listdir(self.audio_dir):
                if filename.endswith(('.wav', '.mp3')):
                    filepath = os.path.join(self.audio_dir, filename)
                    audio_files.append((filepath, os.path.getmtime(filepath)))
            
            # Sort by time (newest first)
            audio_files.sort(key=lambda x: x[1], reverse=True)
            
            # Delete old files beyond the limit
            max_files = Config.MAX_AUDIO_FILES
            if len(audio_files) > max_files:
                for filepath, _ in audio_files[max_files:]:
                    os.remove(filepath)
                    print(f"[CLEANUP] Deleted old audio: {os.path.basename(filepath)}")
        except Exception as e:
            print(f"[WARN] Cleanup error: {e}")
    
    def speak_stream(self, text_stream):
        """
        Stream TTS: speak sentences as they arrive from text stream
        
        Args:
            text_stream: Generator yielding text chunks
        """
        sentence_buffer = ""
        sentence_endings = re.compile(r'[.!?]\s+')
        
        try:
            for chunk in text_stream:
                sentence_buffer += chunk
                
                # Check if we have a complete sentence
                match = sentence_endings.search(sentence_buffer)
                if match:
                    # Extract complete sentence
                    sentence = sentence_buffer[:match.end()].strip()
                    sentence_buffer = sentence_buffer[match.end():]
                    
                    # Speak the sentence immediately
                    if sentence:
                        print(f"[STREAM] {sentence}")
                        self.speak(sentence, save_file=False, play_audio=True)
            
            # Speak any remaining text
            if sentence_buffer.strip():
                print(f"[STREAM] {sentence_buffer}")
                self.speak(sentence_buffer.strip(), save_file=False, play_audio=True)
                
        except Exception as e:
            print(f"[ERROR] Stream TTS error: {e}")
    
    def list_available_models(self):
        """List all available TTS models"""
        print("\n📋 Available TTS models:")
        print("Run: tts --list_models")
        print("\nRecommended fast models:")
        print("  • tts_models/en/ljspeech/tacotron2-DDC")
        print("  • tts_models/en/ljspeech/fast_pitch")
        print("  • tts_models/en/vctk/vits")
    
    def get_model_info(self):
        """Get model information"""
        return {
            "model": self.model_name,
            "gpu": self.use_gpu,
            "audio_dir": self.audio_dir
        }


# Test module
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  [TTS] Coqui TTS Local Test")
    print("="*60 + "\n")
    
    # Initialize
    try:
        tts = LocalTTS()
        
        # Show info
        info = tts.get_model_info()
        print(f"Model: {info['model']}")
        print(f"GPU: {info['gpu']}")
        print(f"Audio dir: {info['audio_dir']}\n")
        
        # Test speech
        test_text = f"Hello! I am {Config.ROBOT_NAME}. This is a test of the local text to speech system. It runs entirely offline and is very fast!"
        
        print("[TTS] Testing TTS...\n")
        audio_path = tts.speak(test_text)
        
        if audio_path:
            print(f"\n[OK] Success! Audio saved to: {audio_path}")
        else:
            print("\n[ERROR] TTS test failed")
            
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        print("\n[TIP] Make sure you have installed TTS:")
        print("   pip install TTS")
