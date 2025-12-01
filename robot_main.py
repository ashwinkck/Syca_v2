"""
Syca v2 - Main Robot Orchestrator
Hybrid local/cloud AI robot with vision, voice, and conversation
"""

import threading
import time
import queue
from datetime import datetime
import cv2
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from config import Config
from modules.hybrid_brain import HybridBrain
from modules.continuous_voice import ContinuousVoiceInput
from modules.local_tts import LocalTTS
from modules.vision import Vision

# ============================================
# INITIALIZE ALL SYSTEMS
# ============================================

print("\n" + "🤖"*30)
print(f"  {Config.ROBOT_NAME} v2 - Hybrid AI Robot")
print("🤖"*30 + "\n")

Config.validate()

# Global state
class RobotState:
    def __init__(self):
        self.current_frame = None
        self.latest_vision_analysis = None
        self.vision_timestamp = None
        self.is_speaking = False
        self.conversation_active = True
        self.last_interaction = None
        self.processing_speech = False

state = RobotState()

# Initialize components
brain = HybridBrain()
vision = Vision()
voice_input = ContinuousVoiceInput(robot_state=state)
voice_output = LocalTTS()

# Vision queue
vision_queue = queue.Queue(maxsize=1)

print(f"✅ {Config.ROBOT_NAME} System Initialized!\n")

# ============================================
# VISION THREADS
# ============================================

def fast_vision_loop():
    """Fast vision capture - never blocks"""
    print("👁️ Starting vision capture...")
    
    analysis_interval = Config.VISION_ANALYSIS_INTERVAL
    last_analysis_time = 0
    
    while state.conversation_active:
        try:
            ret, frame = vision.cap.read()
            
            if ret:
                state.current_frame = frame
                
                current_time = time.time()
                if current_time - last_analysis_time >= analysis_interval:
                    # Only queue if previous analysis is done
                    if vision_queue.empty():
                        temp_path = f"{Config.IMAGE_DIR}/temp_vision.jpg"
                        cv2.imwrite(temp_path, frame)
                        vision_queue.put((temp_path, current_time))
                        last_analysis_time = current_time
            
            time.sleep(0.05)
            
        except Exception as e:
            print(f"❌ Vision error: {e}")
            time.sleep(1)

def vision_analyzer_thread():
    """Background vision analysis"""
    print("🧠 Vision analyzer started...")
    
    while state.conversation_active:
        try:
            # Get from queue (non-blocking with timeout)
            temp_path, timestamp = vision_queue.get(timeout=2)
            
            # Analyze with hybrid brain
            try:
                analysis = brain.analyze_image(
                    temp_path,
                    "Briefly describe what you see in one sentence."
                )
                
                if analysis:
                    state.latest_vision_analysis = analysis
                    state.vision_timestamp = datetime.fromtimestamp(timestamp)
                    print(f"👁️ Vision: {analysis[:60]}...")
                
            except Exception as e:
                print(f"⚠️ Vision analysis error: {e}")
            
        except queue.Empty:
            continue
        except Exception as e:
            print(f"❌ Vision analyzer error: {e}")

# ============================================
# VOICE INTERACTION
# ============================================

def handle_user_speech(user_text):
    """Handle speech input immediately"""
    
    # Skip if already processing
    if state.processing_speech:
        print("⏭️ Already processing, skipping...")
        return
    
    state.processing_speech = True
    
    # Process in separate thread
    threading.Thread(
        target=_process_and_respond,
        args=(user_text,),
        daemon=True
    ).start()

def _process_and_respond(user_text):
    """Process user input and respond"""
    try:
        print(f"\n👤 You: {user_text}")
        
        # Check for exit commands
        exit_words = ["exit", "goodbye", "shutdown", "stop", "quit"]
        if any(word in user_text.lower() for word in exit_words):
            response = "Goodbye! Shutting down."
            voice_output.speak(response)
            state.conversation_active = False
            return
        
        # Get vision context if needed
        vision_keywords = ['see', 'look', 'view', 'front', 'camera', 'what', 'holding', 'show']
        asks_about_vision = any(kw in user_text.lower() for kw in vision_keywords)
        
        image_path = None
        if asks_about_vision and state.latest_vision_analysis:
            if state.vision_timestamp:
                age = (datetime.now() - state.vision_timestamp).total_seconds()
                if age < 30:  # Use vision if less than 30s old
                    image_path = state.current_frame
        
        # Stream response and speak in real-time
        state.is_speaking = True
        try:
            text_stream = brain.chat_stream(user_text, use_vision_context=asks_about_vision, image_path=image_path)
            voice_output.speak_stream(text_stream)
        except Exception as e:
            print(f"[ERROR] Streaming error: {e}")
            # Fallback to non-streaming
            response = generate_response(user_text)
            print(f"🤖 {Config.ROBOT_NAME}: {response}")
            voice_output.speak(response, save_file=True, play_audio=True)
        
        state.is_speaking = False
        state.last_interaction = datetime.now()
        
    except Exception as e:
        print(f"❌ Response error: {e}")
    finally:
        state.processing_speech = False

def generate_response(user_text):
    """Generate AI response with vision context if needed"""
    
    # Check if user is asking about vision
    vision_keywords = ['see', 'look', 'view', 'front', 'camera', 'what', 'holding', 'show']
    asks_about_vision = any(kw in user_text.lower() for kw in vision_keywords)
    
    # Use vision context if available and relevant
    if asks_about_vision and state.latest_vision_analysis:
        # Check if vision is recent (within cache time)
        if state.vision_timestamp:
            age = (datetime.now() - state.vision_timestamp).total_seconds()
            if age <= Config.VISION_CACHE_SECONDS:
                enhanced_message = f"""[Current vision: {state.latest_vision_analysis}]

User question: {user_text}

Respond naturally based on what you can see."""
                return brain.chat(enhanced_message)
    
    # Regular chat
    return brain.chat(user_text)

# ============================================
# MAIN STARTUP
# ============================================

def start_robot():
    """Start all systems"""
    
    print("\n" + "="*60)
    print(f"  🚀 Starting {Config.ROBOT_NAME} v2")
    print("="*60 + "\n")
    
    # Thread 1: Vision capture
    vision_capture_thread = threading.Thread(target=fast_vision_loop, daemon=True)
    vision_capture_thread.start()
    print("✅ Vision: Capturing")
    
    # Thread 2: Vision analyzer
    vision_analyze_thread = threading.Thread(target=vision_analyzer_thread, daemon=True)
    vision_analyze_thread.start()
    print("✅ Vision: Analyzer started")
    
    time.sleep(1)
    
    # Thread 3: Continuous voice
    voice_input.start_listening(handle_user_speech)
    print("✅ Voice: Listening")
    
    print("\n" + "="*60)
    
    # Greeting
    greeting = "Oii Ava here"
    print(f"\n🤖 {greeting}\n")
    voice_output.speak(greeting)
    
    # Keep main thread alive
    print("💬 Conversation started... Say 'exit' to stop\n")
    
    try:
        while state.conversation_active:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    
    # Cleanup
    state.conversation_active = False
    voice_input.stop_listening()
    vision.cleanup()
    
    # Show stats
    print("\n")
    brain.print_stats()
    
    print("\n✅ Shutdown complete")

if __name__ == "__main__":
    try:
        start_robot()
    except KeyboardInterrupt:
        print("\n👋 Interrupted")
        state.conversation_active = False
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
