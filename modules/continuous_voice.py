"""
Continuous Voice Input using Energy Detection
Simpler and more robust than VAD
"""

import queue
import threading
import time
import numpy as np
import sounddevice as sd
import tempfile
import wave
import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import Config
from modules.local_stt import LocalSTT


class ContinuousVoiceInput:
    """Continuous voice input with Energy-based Detection"""
    
    def __init__(self, sample_rate=16000, robot_state=None):
        """
        Initialize continuous voice input
        
        Args:
            sample_rate: Audio sample rate (16000 for Whisper)
            robot_state: Optional RobotState to check if robot is speaking
        """
        self.sample_rate = sample_rate
        self.robot_state = robot_state
        
        # Audio settings
        self.block_size = 4000  # 0.25s chunks
        self.threshold = 0.02   # Volume threshold (adjust if needed)
        self.silence_limit = 2.0 # Seconds of silence to end speech
        
        # Audio buffer
        self.audio_queue = queue.Queue()
        self.is_listening = False
        
        # Initialize Whisper
        print("🎤 Loading Whisper for continuous listening...")
        self.stt = LocalSTT()
        
        print("✅ Continuous voice input initialized (Energy Mode)")
    
    def start_listening(self, callback):
        """Start continuous listening"""
        self.is_listening = True
        
        # Thread 1: Capture audio stream
        capture_thread = threading.Thread(
            target=self._capture_audio_stream,
            daemon=True
        )
        capture_thread.start()
        
        # Thread 2: Process audio
        process_thread = threading.Thread(
            target=self._process_audio_stream,
            args=(callback,),
            daemon=True
        )
        process_thread.start()
        
        print("🎤 Continuous listening started")
    
    def _capture_audio_stream(self):
        """Capture audio continuously"""
        
        def audio_callback(indata, frames, time_info, status):
            if status:
                print(f"⚠️ Audio status: {status}")
            self.audio_queue.put(indata.copy())
        
        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.float32,
            blocksize=self.block_size,
            callback=audio_callback
        ):
            while self.is_listening:
                time.sleep(0.1)
    
    def _process_audio_stream(self, callback):
        """Process audio stream based on volume"""
        
        speech_buffer = []
        silence_start = None
        is_speaking = False
        
        while self.is_listening:
            try:
                # Get audio chunk
                chunk = self.audio_queue.get(timeout=1)
                
                # Calculate volume (RMS)
                volume = np.sqrt(np.mean(chunk**2))
                
                # Check if robot is speaking (Echo Cancellation)
                if self.robot_state and self.robot_state.is_speaking:
                    if is_speaking:
                        # Abort current recording if robot starts talking
                        is_speaking = False
                        speech_buffer = []
                        print("[SKIP] Robot started speaking, aborted user input")
                    continue

                # Speech Logic
                if volume > self.threshold:
                    if not is_speaking:
                        print("🗣️ Speech detected...")
                        is_speaking = True
                    
                    speech_buffer.append(chunk)
                    silence_start = None  # Reset silence timer
                    
                elif is_speaking:
                    # We are in a speech segment, but this chunk is silent
                    speech_buffer.append(chunk)
                    
                    if silence_start is None:
                        silence_start = time.time()
                    
                    # Check if silence has lasted long enough
                    if time.time() - silence_start > self.silence_limit:
                        print("🔄 Processing speech...")
                        
                        # Process the buffer
                        full_audio = np.concatenate(speech_buffer)
                        
                        # Transcribe
                        text = self._recognize_from_numpy(full_audio)
                        
                        if text:
                            print(f"✅ Recognized: {text}")
                            callback(text)
                        
                        # Reset
                        is_speaking = False
                        speech_buffer = []
                        silence_start = None
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Audio processing error: {e}")
                continue
    
    def _recognize_from_numpy(self, audio_data):
        """Convert numpy array to text using Whisper"""
        try:
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_path = tmp_file.name
                
                # Write WAV file
                with wave.open(tmp_path, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(self.sample_rate)
                    # Convert float32 -> int16
                    audio_int16 = (audio_data * 32767).astype(np.int16)
                    wav_file.writeframes(audio_int16.tobytes())
            
            # Transcribe
            text = self.stt.transcribe_file(tmp_path)
            
            # Clean up
            os.unlink(tmp_path)
            return text
            
        except Exception as e:
            print(f"❌ Recognition error: {e}")
            return None
    
    def stop_listening(self):
        """Stop continuous listening"""
        self.is_listening = False
        print("🔇 Continuous listening stopped")
