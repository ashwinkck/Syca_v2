"""
Cloud Fallback - OpenRouter and ElevenLabs APIs
Used when local models are unavailable or for complex tasks
"""

import requests
import base64
import os
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))
from config import Config


class CloudFallback:
    """Cloud API fallback for advanced tasks"""
    
    def __init__(self):
        """Initialize cloud APIs"""
        
        # OpenRouter for chat/vision
        self.openrouter_key = Config.OPENROUTER_API_KEY
        self.openrouter_url = Config.OPENROUTER_BASE_URL
        self.chat_model = Config.CLOUD_CHAT_MODEL
        self.vision_model = Config.CLOUD_VISION_MODEL
        
        # ElevenLabs for premium TTS
        self.elevenlabs_key = Config.ELEVENLABS_API_KEY
        self.elevenlabs_voice = Config.ELEVENLABS_VOICE_ID
        
        # Conversation history
        self.conversation_history = []
        
        # Validate
        if not self.openrouter_key:
            raise ValueError("OpenRouter API key not configured")
        
        print("✅ Cloud fallback initialized")
        print(f"   • OpenRouter: {self.chat_model}")
        if self.elevenlabs_key:
            print(f"   • ElevenLabs: {self.elevenlabs_voice}")
    
    def chat(self, message, system_prompt=None):
        """
        Chat using OpenRouter
        
        Args:
            message: User message
            system_prompt: Optional system prompt
            
        Returns:
            str: AI response
        """
        try:
            # Build messages
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.extend(self.conversation_history)
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Call OpenRouter
            response = requests.post(
                f"{self.openrouter_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.chat_model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 500
                },
                timeout=Config.CLOUD_TIMEOUT
            )
            
            response.raise_for_status()
            result = response.json()
            assistant_message = result["choices"][0]["message"]["content"]
            
            # Update history
            self.conversation_history.append({
                "role": "user",
                "content": message
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            # Keep history manageable
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            return assistant_message
        
        except Exception as e:
            print(f"[ERROR] Chat error: {e}")
            return None
    
    def chat_stream(self, message, system_prompt=None):
        """
        Stream chat responses from OpenRouter in real-time
        
        Args:
            message: User message
            system_prompt: Optional system prompt
            
        Yields:
            str: Text chunks as they arrive
        """
        try:
            # Build messages
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.extend(self.conversation_history)
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Call OpenRouter with streaming
            response = requests.post(
                f"{self.openrouter_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.chat_model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 500,
                    "stream": True
                },
                stream=True,
                timeout=Config.CLOUD_TIMEOUT
            )
            
            response.raise_for_status()
            
            # Stream response
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]  # Remove 'data: ' prefix
                        if data_str == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    full_response += content
                                    yield content
                        except json.JSONDecodeError:
                            continue
            
            # Update history with full response
            self.conversation_history.append({
                "role": "user",
                "content": message
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": full_response
            })
            
            # Keep history manageable
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
        except Exception as e:
            print(f"❌ Cloud chat error: {e}")
            return None
    
    def analyze_image(self, image_path, question="What do you see?"):
        """
        Analyze image using OpenRouter vision model
        
        Args:
            image_path: Path to image
            question: Question about image
            
        Returns:
            str: Vision analysis
        """
        try:
            # Read and encode image
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            # Call OpenRouter vision API
            response = requests.post(
                f"{self.openrouter_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.vision_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": question
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_data}"
                                    }
                                }
                            ]
                        }
                    ],
                    "temperature": 0.5,
                    "max_tokens": 800
                },
                timeout=Config.CLOUD_TIMEOUT
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            print(f"❌ Cloud vision error: {e}")
            return None
    
    def chat_with_vision(self, message, image_path):
        """
        Chat with image context
        
        Args:
            message: User message
            image_path: Image path
            
        Returns:
            str: AI response
        """
        # Analyze image first
        vision_context = self.analyze_image(
            image_path,
            "Describe what you see in detail."
        )
        
        if vision_context:
            enhanced_message = f"[I can see: {vision_context}]\n\nUser: {message}"
            return self.chat(enhanced_message)
        else:
            return self.chat(message)
    
    def speak_premium(self, text, save_file=True):
        """
        Premium TTS using ElevenLabs
        
        Args:
            text: Text to speak
            save_file: Save audio file
            
        Returns:
            str: Path to audio file
        """
        if not self.elevenlabs_key:
            print("⚠️ ElevenLabs API key not configured")
            return None
        
        try:
            response = requests.post(
                f"{Config.ELEVENLABS_TTS_URL}/{self.elevenlabs_voice}",
                headers={
                    "xi-api-key": self.elevenlabs_key,
                    "Content-Type": "application/json"
                },
                json={
                    "text": text,
                    "model_id": Config.ELEVENLABS_MODEL,
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75
                    }
                },
                timeout=30
            )
            
            response.raise_for_status()
            
            if save_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                audio_path = os.path.join(Config.AUDIO_DIR, f"premium_{timestamp}.mp3")
                
                with open(audio_path, "wb") as f:
                    f.write(response.content)
                
                print(f"✅ Premium audio saved: {audio_path}")
                return audio_path
            
            return response.content
            
        except Exception as e:
            print(f"❌ Premium TTS error: {e}")
            return None
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []


# Test module
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  ☁️ Cloud Fallback Test")
    print("="*60 + "\n")
    
    Config.validate()
    
    try:
        cloud = CloudFallback()
        
        # Test chat
        print("\n🧪 Testing cloud chat...\n")
        response = cloud.chat(
            "Hello! Respond in one sentence.",
            system_prompt=Config.get_system_prompt()
        )
        
        if response:
            print(f"\n🤖 Response: {response}")
        else:
            print("\n❌ Cloud chat failed")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
