"""
Raspberry Pi Client for Ava Robot
Captures camera + microphone and streams to PC for AI processing
"""

import cv2
import sounddevice as sd
import numpy as np
import requests
import websocket
import threading
import time
import argparse
import json
from datetime import datetime

class PiClient:
    """Lightweight client for Raspberry Pi sensors"""
    
    def __init__(self, server_url="http://192.168.1.100:8000"):
        """
        Initialize Pi client
        
        Args:
            server_url: PC server URL (e.g., http://192.168.1.100:8000)
        """
        self.server_url = server_url
        self.ws_url = server_url.replace("http://", "ws://").replace("https://", "wss://")
        
        # Camera setup
        print("📷 Initializing camera...")
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.camera.set(cv2.CAP_PROP_FPS, 30)
        
        if not self.camera.isOpened():
            raise RuntimeError("❌ Failed to open camera")
        print("✅ Camera ready")
        
        # Audio setup
        print("🎤 Initializing audio...")
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_size = 4000  # 0.25s chunks
        print("✅ Audio ready")
        
        # State
        self.running = False
        self.ws = None
        
    def connect_websocket(self):
        """Connect to PC WebSocket for audio streaming"""
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                print(f"🔌 Connecting to {self.ws_url}/audio/stream...")
                self.ws = websocket.WebSocket()
                self.ws.connect(f"{self.ws_url}/audio/stream")
                print("✅ WebSocket connected")
                return True
            except Exception as e:
                retry_count += 1
                print(f"⚠️ Connection failed (attempt {retry_count}/{max_retries}): {e}")
                time.sleep(2)
        
        return False
    
    def stream_video(self):
        """Stream video frames to PC"""
        print("📹 Starting video stream...")
        frame_count = 0
        
        while self.running:
            try:
                ret, frame = self.camera.read()
                
                if not ret:
                    print("⚠️ Failed to capture frame")
                    time.sleep(0.1)
                    continue
                
                # Encode as JPEG (compress for network)
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                
                # Send to PC
                response = requests.post(
                    f"{self.server_url}/video/frame",
                    data=buffer.tobytes(),
                    timeout=1
                )
                
                frame_count += 1
                if frame_count % 25 == 0:  # Every 5 seconds
                    print(f"📹 Sent {frame_count} frames")
                
                # 5 FPS (save bandwidth)
                time.sleep(0.2)
                
            except requests.exceptions.Timeout:
                print("⚠️ Video upload timeout")
            except Exception as e:
                print(f"❌ Video error: {e}")
                time.sleep(1)
    
    def stream_audio(self):
        """Stream audio to PC and receive responses"""
        print("🎤 Starting audio stream...")
        
        def audio_callback(indata, frames, time_info, status):
            """Called for each audio chunk"""
            if status:
                print(f"⚠️ Audio status: {status}")
            
            try:
                # Send audio to PC
                if self.ws and self.running:
                    # Convert float32 to int16 for smaller size
                    audio_int16 = (indata * 32767).astype(np.int16)
                    self.ws.send_binary(audio_int16.tobytes())
            except Exception as e:
                print(f"❌ Audio send error: {e}")
        
        # Start audio input stream
        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=np.float32,
            blocksize=self.chunk_size,
            callback=audio_callback
        ):
            print("✅ Audio streaming active")
            
            # Receive and play audio responses from PC
            while self.running:
                try:
                    if self.ws:
                        # Receive audio from PC
                        message = self.ws.recv()
                        
                        if message:
                            # Parse message
                            data = json.loads(message)
                            
                            if data.get('type') == 'audio':
                                # Play audio response
                                audio_data = np.frombuffer(
                                    bytes.fromhex(data['data']),
                                    dtype=np.float32
                                )
                                print(f"🔊 Playing response ({len(audio_data)} samples)")
                                sd.play(audio_data, samplerate=data.get('samplerate', 22050))
                                sd.wait()
                            
                            elif data.get('type') == 'text':
                                # Display transcription
                                print(f"💬 Ava: {data['text']}")
                
                except websocket.WebSocketTimeoutException:
                    continue
                except Exception as e:
                    print(f"❌ Audio receive error: {e}")
                    time.sleep(1)
    
    def start(self):
        """Start all streaming threads"""
        print("\n" + "="*60)
        print("  🤖 Ava Pi Client Starting")
        print("="*60 + "\n")
        
        # Connect WebSocket
        if not self.connect_websocket():
            print("❌ Failed to connect to server")
            return
        
        self.running = True
        
        # Start video thread
        video_thread = threading.Thread(target=self.stream_video, daemon=True)
        video_thread.start()
        print("✅ Video thread started")
        
        # Start audio thread (blocks)
        try:
            self.stream_audio()
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
        finally:
            self.stop()
    
    def stop(self):
        """Stop all streaming"""
        self.running = False
        
        if self.ws:
            self.ws.close()
        
        if self.camera:
            self.camera.release()
        
        print("✅ Stopped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ava Pi Client")
    parser.add_argument(
        "--server",
        type=str,
        default="http://192.168.1.100:8000",
        help="PC server URL (default: http://192.168.1.100:8000)"
    )
    
    args = parser.parse_args()
    
    try:
        client = PiClient(server_url=args.server)
        client.start()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
