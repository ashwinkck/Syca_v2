# 🚀 Syca v2 Installation Guide

Follow these steps to set up the hybrid AI robot with local models.

## Step 1: Install Python Dependencies

```powershell
pip install -r requirements.txt
```

**Note**: This will download several large packages (PyTorch, Whisper, TTS). It may take 5-10 minutes.

## Step 2: Install Ollama

Ollama provides fast local LLMs.

1. **Download Ollama**:
   - Visit: https://ollama.ai
   - Download for Windows
   - Run the installer

2. **Start Ollama**:
   ```powershell
   ollama serve
   ```
   
   Keep this running in a separate terminal.

3. **Pull Models**:
   ```powershell
   # Chat model (choose one)
   ollama pull llama3.2          # Recommended (fast, good quality)
   # OR
   ollama pull mistral           # Alternative (also good)
   
   # Vision model
   ollama pull llava             # Required for vision
   ```

## Step 3: Configure Environment

1. **Copy the example env file**:
   ```powershell
   Copy-Item .env.example .env
   ```

2. **Edit `.env`** (optional - only if you want cloud fallback):
   - Add your `OPENROUTER_API_KEY` (from v1 if you have it)
   - Add your `ELEVENLABS_API_KEY` (from v1 if you have it)

## Step 4: Test Components

Test each component individually:

```powershell
# Test Ollama connection
python modules/local_llm.py

# Test Whisper STT (will download model on first run)
python modules/local_stt.py

# Test Coqui TTS (will download model on first run)
python modules/local_tts.py

# Test hybrid brain
python modules/hybrid_brain.py
```

## Step 5: Run the Robot

```powershell
# Full robot mode (coming soon)
python robot_main.py

# Or test configuration
python config.py
```

## Troubleshooting

### Ollama Connection Error
```
❌ Cannot connect to Ollama at http://localhost:11434
```

**Solution**: Make sure Ollama is running:
```powershell
ollama serve
```

### Whisper Model Download
On first run, Whisper will download the model (~150MB for 'base'). This is normal.

### TTS Model Download
On first run, Coqui TTS will download the model (~100MB). This is normal.

### GPU Support (Optional)

If you have an NVIDIA GPU, you can enable GPU acceleration:

1. **Install CUDA-enabled PyTorch**:
   ```powershell
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```

2. **Update `.env`**:
   ```
   WHISPER_DEVICE=cuda
   TTS_USE_GPU=true
   ```

## Model Sizes

### Whisper Models (Speed vs Accuracy)
- `tiny`: 39M params, ~0.1s, least accurate
- `base`: 74M params, ~0.3s, **recommended**
- `small`: 244M params, ~0.8s, better
- `medium`: 769M params, ~2s, best quality
- `large`: 1550M params, ~5s, highest quality

### Ollama Models
- `llama3.2`: 3B params, fast, good quality
- `mistral`: 7B params, balanced
- `llava`: Vision model (required for camera)

## What's Next?

Once everything is installed and tested, you can:
1. Run the full robot with `python robot_main.py`
2. Customize the personality in `config.py`
3. Adjust performance settings in `.env`

---

**Need help?** Check the main README.md or test individual modules first.
