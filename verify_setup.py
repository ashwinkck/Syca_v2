"""
Quick Setup Test - Verify all components are working
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

def test_config():
    """Test configuration"""
    print("\n" + "="*60)
    print("  1️⃣ Testing Configuration")
    print("="*60)
    
    try:
        from config import Config
        Config.validate()
        return True
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def test_ollama():
    """Test Ollama connection"""
    print("\n" + "="*60)
    print("  2️⃣ Testing Ollama (Local LLM)")
    print("="*60)
    
    try:
        from modules.local_llm import LocalLLM
        llm = LocalLLM()
        
        # Quick test
        response = llm.chat("Say 'hello' in one word.", system_prompt="You are a helpful assistant.")
        
        if response:
            print(f"✅ Ollama working! Response: {response}")
            return True
        else:
            print("❌ Ollama returned no response")
            return False
            
    except Exception as e:
        print(f"❌ Ollama error: {e}")
        print("\n💡 Make sure Ollama is running:")
        print("   1. Download from: https://ollama.ai")
        print("   2. Run: ollama serve")
        print("   3. Pull model: ollama pull llama3.2")
        return False

def test_whisper():
    """Test Whisper (will download model on first run)"""
    print("\n" + "="*60)
    print("  3️⃣ Testing Whisper (Local STT)")
    print("="*60)
    
    try:
        from modules.local_stt import LocalSTT
        
        print("⏳ Loading Whisper model (may download on first run)...")
        stt = LocalSTT()
        
        info = stt.get_model_info()
        print(f"✅ Whisper ready!")
        print(f"   • Model: {info['model']}")
        print(f"   • Device: {info['device']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Whisper error: {e}")
        print("\n💡 Install Whisper:")
        print("   pip install openai-whisper")
        return False

def test_tts():
    """Test Coqui TTS (will download model on first run)"""
    print("\n" + "="*60)
    print("  4️⃣ Testing Coqui TTS (Local Text-to-Speech)")
    print("="*60)
    
    try:
        from modules.local_tts import LocalTTS
        
        print("⏳ Loading TTS model (may download on first run)...")
        tts = LocalTTS()
        
        info = tts.get_model_info()
        print(f"✅ TTS ready!")
        print(f"   • Model: {info['model']}")
        print(f"   • GPU: {info['gpu']}")
        
        return True
        
    except Exception as e:
        print(f"❌ TTS error: {e}")
        print("\n💡 Install TTS:")
        print("   pip install TTS")
        return False

def test_hybrid_brain():
    """Test hybrid brain"""
    print("\n" + "="*60)
    print("  5️⃣ Testing Hybrid Brain")
    print("="*60)
    
    try:
        from modules.hybrid_brain import HybridBrain
        
        brain = HybridBrain()
        
        # Quick test
        response = brain.chat("What's 2+2? Answer in one sentence.")
        
        if response:
            print(f"✅ Hybrid brain working!")
            print(f"   Response: {response}")
            
            # Show stats
            brain.print_stats()
            return True
        else:
            print("❌ No response from hybrid brain")
            return False
            
    except Exception as e:
        print(f"❌ Hybrid brain error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "🚀"*30)
    print("  SYCA V2 - SETUP VERIFICATION")
    print("🚀"*30)
    
    results = {
        "Config": test_config(),
        "Ollama": test_ollama(),
        "Whisper": test_whisper(),
        "TTS": test_tts(),
        "Hybrid Brain": test_hybrid_brain()
    }
    
    # Summary
    print("\n" + "="*60)
    print("  📊 SETUP SUMMARY")
    print("="*60)
    
    for component, status in results.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {component}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All components working! You're ready to go!")
        print("\n📝 Next steps:")
        print("   • Run the full robot: python robot_main.py")
        print("   • Or continue testing individual modules")
    else:
        print("\n⚠️ Some components failed. Check errors above.")
        print("\n💡 See INSTALL.md for detailed setup instructions")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
