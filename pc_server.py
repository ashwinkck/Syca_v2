"""
PC Server for Ava Robot
Receives camera/audio from Raspberry Pi and processes with AI models
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
import uvicorn
import cv2
import numpy as np
import json
import asyncio
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from config import Config
from modules.hybrid_brain import HybridBrain
from modules.local_stt import LocalSTT
from modules.local_tts import LocalTTS

# Initialize FastAPI
app = FastAPI(title="Ava PC Server")

# Initialize AI components
print("\n" + "🤖"*30)
print(f"  {Config.ROBOT_NAME} PC Server")
print("🤖"*30 + "\n")

Config.validate()

brain = HybridBrain()
stt = LocalSTT()
tts = LocalTTS()

# State
latest_frame = None
latest_vision = None
audio_buffer = []

print("✅ Server initialized\n")


@app.get("/")
async def root():
    """Health check"""
    return {"status": "ok", "robot": Config.ROBOT_NAME, "mode": "server"}


@app.post("/video/frame")
async def receive_frame(request: Request):
    """
    Receive video frame from Pi
    
    Args:
        request: Raw JPEG image bytes in request body
    """
    global latest_frame, latest_vision
    
    try:
        # Read raw bytes from request body
        data = await request.body()
        
        # Decode JPEG
        nparr = np.frombuffer(data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return JSONResponse({"error": "Invalid image"}, status_code=400)
        
        latest_frame = frame
        
        # Analyze with vision model (async, don't block)
        try:
            # Save temp file
            temp_path = f"{Config.IMAGE_DIR}/pi_frame_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(temp_path, frame)
            
            # Analyze
            analysis = brain.analyze_image(temp_path, "Briefly describe what you see.")
            latest_vision = {
                "text": analysis,
                "timestamp": datetime.now()
            }
            print(f"👁️ Vision: {analysis[:60]}...")
            
        except Exception as e:
            print(f"⚠️ Vision error: {e}")
        
        return {"status": "ok", "shape": frame.shape}
    
    except Exception as e:
        print(f"❌ Frame error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.websocket("/audio/stream")
async def audio_stream(websocket: WebSocket):
    """
    WebSocket for bidirectional audio streaming
    
    Pi → PC: Audio chunks for transcription
    PC → Pi: TTS audio responses
    """
    await websocket.accept()
    print("🔌 Pi connected via WebSocket")
    
    audio_buffer = []
    silence_count = 0
    silence_threshold = 8  # 2 seconds of silence
    
    try:
        while True:
            # Receive audio from Pi
            data = await websocket.receive_bytes()
            
            # Convert bytes to numpy array
            audio_chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32767.0
            
            # Calculate volume
            volume = np.sqrt(np.mean(audio_chunk**2))
            
            # Speech detection
            if volume > 0.02:  # Speech detected
                audio_buffer.append(audio_chunk)
                silence_count = 0
            elif len(audio_buffer) > 0:  # In speech, but silent chunk
                audio_buffer.append(audio_chunk)
                silence_count += 1
                
                # End of speech
                if silence_count >= silence_threshold:
                    print("🔄 Processing speech...")
                    
                    # Concatenate audio
                    full_audio = np.concatenate(audio_buffer)
                    
                    # Transcribe with Whisper
                    try:
                        import tempfile
                        import wave
                        import os
                        
                        # Create temp file
                        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".wav")
                        
                        try:
                            # Write WAV file
                            with wave.open(tmp_path, 'wb') as wav:
                                wav.setnchannels(1)
                                wav.setsampwidth(2)
                                wav.setframerate(16000)
                                audio_int16 = (full_audio * 32767).astype(np.int16)
                                wav.writeframes(audio_int16.tobytes())
                            
                            # Close the file descriptor
                            os.close(tmp_fd)
                            
                            # Now transcribe (file is fully closed)
                            text = stt.transcribe_file(tmp_path)
                        
                        finally:
                            # Cleanup temp file
                            if os.path.exists(tmp_path):
                                os.unlink(tmp_path)
                        
                        if text:
                            print(f"👤 User: {text}")
                            
                            # Generate response with vision context if available
                            image_path = None
                            if latest_vision:
                                age = (datetime.now() - latest_vision['timestamp']).total_seconds()
                                if age < 30:  # Use vision if recent
                                    # Check if user asks about vision
                                    vision_keywords = ['see', 'look', 'what', 'view', 'show']
                                    if any(kw in text.lower() for kw in vision_keywords):
                                        # Inject vision context
                                        text = f"[SYSTEM: You see: {latest_vision['text']}]\n\nUser: {text}"
                            
                            # Stream response
                            response_text = ""
                            for chunk in brain.chat_stream(text):
                                response_text += chunk
                            
                            print(f"🤖 Ava: {response_text}")
                            
                            # Send text response
                            await websocket.send_text(json.dumps({
                                "type": "text",
                                "text": response_text
                            }))
                            
                            # Generate TTS
                            try:
                                audio_path = tts.speak(response_text, save_file=False, play_audio=False)
                                
                                if audio_path:
                                    # Read audio file
                                    import soundfile as sf
                                    audio_data, sr = sf.read(audio_path)
                                    
                                    # Send audio to Pi
                                    await websocket.send_text(json.dumps({
                                        "type": "audio",
                                        "data": audio_data.tobytes().hex(),
                                        "samplerate": sr
                                    }))
                                    
                                    # Cleanup
                                    import os
                                    os.unlink(audio_path)
                            
                            except Exception as e:
                                print(f"⚠️ TTS error: {e}")
                    
                    except Exception as e:
                        print(f"❌ Transcription error: {e}")
                    
                    # Reset buffer
                    audio_buffer = []
                    silence_count = 0
    
    except WebSocketDisconnect:
        print("🔌 Pi disconnected")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  🚀 Starting Ava PC Server")
    print("="*60 + "\n")
    print(f"Server will run on: http://0.0.0.0:8000")
    print(f"WebSocket endpoint: ws://0.0.0.0:8000/audio/stream")
    print("\nWaiting for Pi client to connect...\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
