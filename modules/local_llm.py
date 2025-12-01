"""
Local LLM using Ollama
Fast chat and vision capabilities running locally
"""

import requests
import json
import base64
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import Config


class LocalLLM:
    """Local LLM interface using Ollama"""
    
    def __init__(self, host=None):
        """
        Initialize Ollama client
        
        Args:
            host: Ollama host URL (default from config)
        """
        self.host = host or Config.OLLAMA_HOST
        self.chat_model = Config.OLLAMA_CHAT_MODEL
        self.vision_model = Config.OLLAMA_VISION_MODEL
        self.conversation_history = []
        
        # Check if Ollama is running
        if not self._check_ollama():
            raise ConnectionError(
                f"❌ Cannot connect to Ollama at {self.host}\n"
                "💡 Make sure Ollama is running: 'ollama serve'"
            )
        
        print(f"✅ Ollama connected ({self.host})")
        print(f"   • Chat model: {self.chat_model}")
        print(f"   • Vision model: {self.vision_model}")
    
    def _check_ollama(self):
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def chat(self, message, system_prompt=None, stream=False):
        """
        Chat with local LLM
        
        Args:
            message: User message
            system_prompt: System prompt (optional)
            stream: Stream response (default: False)
            
        Returns:
            str: AI response
        """
        try:
            # Build messages
            messages = []
            
            # Add system prompt if provided
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # Add conversation history
            messages.extend(self.conversation_history)
            
            # Add user message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Call Ollama API
            response = requests.post(
                f"{self.host}/api/chat",
                json={
                    "model": self.chat_model,
                    "messages": messages,
                    "stream": stream
                },
                timeout=30
            )
            
            response.raise_for_status()
            
            # Parse response
            if stream:
                # Handle streaming response
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        if "message" in data:
                            chunk = data["message"].get("content", "")
                            full_response += chunk
                            print(chunk, end="", flush=True)
                print()  # New line after streaming
                assistant_message = full_response
            else:
                # Handle non-streaming response
                result = response.json()
                assistant_message = result["message"]["content"]
            
            # Update conversation history
            self.conversation_history.append({
                "role": "user",
                "content": message
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            # Keep history manageable (last 10 messages)
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            return assistant_message
            
        except Exception as e:
            print(f"❌ Chat error: {e}")
            return None
    
    def analyze_image(self, image_path, question="What do you see in this image?"):
        """
        Analyze image using vision model
        
        Args:
            image_path: Path to image file
            question: Question about the image
            
        Returns:
            str: Vision analysis
        """
        try:
            # Read and encode image
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            # Call Ollama vision API
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.vision_model,
                    "prompt": question,
                    "images": [image_data],
                    "stream": False
                },
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result.get("response", "").strip()
            
        except Exception as e:
            print(f"❌ Vision error: {e}")
            return None
    
    def chat_with_vision(self, message, image_path=None):
        """
        Chat with optional image context
        
        Args:
            message: User message
            image_path: Optional image path
            
        Returns:
            str: AI response
        """
        if image_path and os.path.exists(image_path):
            # First, analyze the image
            vision_context = self.analyze_image(
                image_path,
                "Describe what you see in detail."
            )
            
            if vision_context:
                # Add vision context to message
                enhanced_message = f"[I can see: {vision_context}]\n\nUser question: {message}"
                return self.chat(enhanced_message)
        
        # No image or vision failed, use regular chat
        return self.chat(message)
    
    def reset_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("🔄 Conversation reset")
    
    def list_models(self):
        """List available Ollama models"""
        try:
            response = requests.get(f"{self.host}/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            
            print("\n📋 Available Ollama models:")
            for model in models:
                print(f"  • {model['name']}")
            
            return models
        except Exception as e:
            print(f"❌ Error listing models: {e}")
            return []
    
    def get_model_info(self):
        """Get model information"""
        return {
            "host": self.host,
            "chat_model": self.chat_model,
            "vision_model": self.vision_model,
            "history_length": len(self.conversation_history)
        }


# Test module
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  🧠 Ollama Local LLM Test")
    print("="*60 + "\n")
    
    try:
        # Initialize
        llm = LocalLLM()
        
        # Show info
        info = llm.get_model_info()
        print(f"\nHost: {info['host']}")
        print(f"Chat model: {info['chat_model']}")
        print(f"Vision model: {info['vision_model']}\n")
        
        # List available models
        llm.list_models()
        
        # Test chat
        print("\n🧪 Testing chat...\n")
        response = llm.chat(
            "Hello! Introduce yourself in one sentence.",
            system_prompt=Config.get_system_prompt()
        )
        
        if response:
            print(f"\n🤖 Response: {response}")
        else:
            print("\n❌ Chat test failed")
        
        # Test follow-up
        print("\n🧪 Testing follow-up...\n")
        response = llm.chat("What can you help me with?")
        
        if response:
            print(f"\n🤖 Response: {response}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure Ollama is installed and running:")
        print("   1. Download from: https://ollama.ai")
        print("   2. Run: ollama serve")
        print("   3. Pull models: ollama pull llama3.2")
        print("                   ollama pull llava")
