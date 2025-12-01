"""
Hybrid Brain - Intelligent routing between local and cloud models
Optimizes for speed while maintaining quality
"""

import time
import sys
from pathlib import Path

# Add parent directory to path for config import
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import Config

# Import local models
from modules.local_llm import LocalLLM

# Import cloud fallback (optional)
try:
    from modules.cloud_fallback import CloudFallback
    CLOUD_AVAILABLE = True
except ImportError:
    CLOUD_AVAILABLE = False
    print("[WARN] Cloud fallback not available (missing API keys)")


class HybridBrain:
    """
    Intelligent AI brain that routes requests to local or cloud models
    based on complexity, performance, and availability
    """
    
    def __init__(self):
        """Initialize hybrid brain with local and cloud models"""
        
        print("\n[BRAIN] Initializing Hybrid Brain...")
        
        # Initialize local models (primary)
        try:
            self.local_llm = LocalLLM()
            self.local_available = True
        except Exception as e:
            print(f"[WARN] Local LLM not available: {e}")
            self.local_available = False
        
        # Initialize cloud fallback (optional)
        self.cloud_available = False
        if Config.USE_CLOUD_FALLBACK and CLOUD_AVAILABLE:
            try:
                self.cloud = CloudFallback()
                self.cloud_available = True
            except Exception as e:
                print(f"[WARN] Cloud fallback not available: {e}")
        
        # Statistics
        self.stats = {
            "local_requests": 0,
            "cloud_requests": 0,
            "local_failures": 0,
            "cloud_failures": 0
        }
        
        print(f"[OK] Hybrid Brain ready")
        print(f"   - Local: {'[OK]' if self.local_available else '[NO]'}")
        print(f"   - Cloud: {'[OK]' if self.cloud_available else '[NO]'}")
        print(f"   - Mode: {Config.MODE}")
    
    def chat(self, message, use_vision_context=False, image_path=None):
        """
        Chat with intelligent routing
        
        Args:
            message: User message
            use_vision_context: Include vision context
            image_path: Optional image path
            
        Returns:
            str: AI response
        """
        
        # Determine routing strategy
        use_cloud = self._should_use_cloud(message)
        
        # Try local first (unless quality mode forces cloud)
        if not use_cloud and self.local_available:
            response = self._chat_local(message, image_path)
            if response:
                self.stats["local_requests"] += 1
                return response
            else:
                self.stats["local_failures"] += 1
                print("[WARN] Local chat failed, trying cloud...")
        
        # Fallback to cloud
        if self.cloud_available:
            response = self._chat_cloud(message, image_path)
            if response:
                self.stats["cloud_requests"] += 1
                return response
            else:
                self.stats["cloud_failures"] += 1
        
        return "I'm having trouble processing that right now. Please try again."
    
    def chat_stream(self, message, use_vision_context=False, image_path=None):
        """
        Stream chat responses in real-time
        
        Args:
            message: User message
            use_vision_context: Include vision context
            image_path: Optional image path
            
        Yields:
            str: Text chunks as they arrive
        """
        # For now, only cloud supports streaming
        if self.cloud_available:
            try:
                # Inject vision context if provided
                if image_path:
                    vision_context = self.analyze_image(image_path, "Describe this image in detail.")
                    if vision_context:
                        print(f"👁️ Vision Context: {vision_context[:50]}...")
                        message = f"[SYSTEM: You see the following: {vision_context}]\n\nUser: {message}"
                
                # Stream from cloud
                for chunk in self.cloud.chat_stream(message, system_prompt=Config.get_system_prompt()):
                    yield chunk
                    
                self.stats["cloud_requests"] += 1
                return
            except Exception as e:
                print(f"[ERROR] Stream error: {e}")
                self.stats["cloud_failures"] += 1
        
        # Fallback to non-streaming
        response = self.chat(message, use_vision_context, image_path)
        if response:
            yield response
    
    def analyze_image(self, image_path, question="What do you see?"):
        """
        Analyze image with intelligent routing
        
        Args:
            image_path: Path to image
            question: Question about image
            
        Returns:
            str: Vision analysis
        """
        
        # Try local vision first
        if self.local_available:
            start_time = time.time()
            result = self.local_llm.analyze_image(image_path, question)
            elapsed = time.time() - start_time
            
            if result:
                print(f"[OK] Local vision: {elapsed:.2f}s")
                self.stats["local_requests"] += 1
                return result
            else:
                self.stats["local_failures"] += 1
                print("[WARN] Local vision failed, trying cloud...")
        
        # Fallback to cloud
        if self.cloud_available:
            start_time = time.time()
            result = self.cloud.analyze_image(image_path, question)
            elapsed = time.time() - start_time
            
            if result:
                print(f"[OK] Cloud vision: {elapsed:.2f}s")
                self.stats["cloud_requests"] += 1
                return result
            else:
                self.stats["cloud_failures"] += 1
        
        return "I couldn't analyze the image."
    
    def _should_use_cloud(self, message):
        """
        Determine if cloud should be used based on message complexity
        
        Args:
            message: User message
            
        Returns:
            bool: True if cloud should be used
        """
        
        # Force cloud in quality mode
        if Config.MODE == "quality":
            return True
        
        # Force local in speed mode
        if Config.MODE == "speed":
            return False
        
        # Balanced mode: analyze complexity
        complexity_keywords = [
            "analyze", "complex", "detailed", "explain in depth",
            "comprehensive", "thorough", "research", "document"
        ]
        
        message_lower = message.lower()
        is_complex = any(kw in message_lower for kw in complexity_keywords)
        
        # Use cloud for complex queries if available
        return is_complex and self.cloud_available
    
    def _chat_local(self, message, image_path=None):
        """Chat using local LLM"""
        try:
            if image_path:
                return self.local_llm.chat_with_vision(message, image_path)
            else:
                return self.local_llm.chat(
                    message,
                    system_prompt=Config.get_system_prompt()
                )
        except Exception as e:
            print(f"[ERROR] Local chat error: {e}")
            return None
    
    def _chat_cloud(self, message, image_path=None):
        """Chat using cloud fallback"""
        
        # If image provided, get vision analysis first
        vision_context = ""
        if image_path:
            vision_context = self.analyze_image(image_path, "Describe this image in detail.")
            if vision_context:
                print(f"👁️ Vision Context: {vision_context[:50]}...")
                # CRITICAL: Inject vision directly into user message to force acknowledgement
                message = f"[SYSTEM: You see the following: {vision_context}]\n\nUser: {message}"
        
        return self.cloud.chat(message, system_prompt=Config.get_system_prompt())
    
    def reset_conversation(self):
        """Reset conversation history"""
        if self.local_available:
            self.local_llm.reset_conversation()
        if self.cloud_available:
            self.cloud.reset_conversation()
        print("[INFO] Conversation reset")
    
    def get_stats(self):
        """Get usage statistics"""
        total = self.stats["local_requests"] + self.stats["cloud_requests"]
        
        if total == 0:
            return "No requests yet"
        
        local_pct = (self.stats["local_requests"] / total) * 100
        cloud_pct = (self.stats["cloud_requests"] / total) * 100
        
        return {
            "total_requests": total,
            "local_requests": self.stats["local_requests"],
            "cloud_requests": self.stats["cloud_requests"],
            "local_percentage": f"{local_pct:.1f}%",
            "cloud_percentage": f"{cloud_pct:.1f}%",
            "local_failures": self.stats["local_failures"],
            "cloud_failures": self.stats["cloud_failures"]
        }
    
    def print_stats(self):
        """Print usage statistics"""
        stats = self.get_stats()
        
        if isinstance(stats, str):
            print(stats)
            return
        
        print("\n[STATS] Hybrid Brain Statistics:")
        print(f"   - Total requests: {stats['total_requests']}")
        print(f"   - Local: {stats['local_requests']} ({stats['local_percentage']})")
        print(f"   - Cloud: {stats['cloud_requests']} ({stats['cloud_percentage']})")
        print(f"   - Failures: {stats['local_failures']} local, {stats['cloud_failures']} cloud")
