"""
Microphone Test - Check audio input levels and devices
"""

import sounddevice as sd
import numpy as np
import time

print("\n" + "="*60)
print("  Microphone Diagnostic Tool")
print("="*60 + "\n")

# List all audio devices
print("Available audio devices:")
print("-" * 60)
devices = sd.query_devices()
for i, device in enumerate(devices):
    if device['max_input_channels'] > 0:
        default = " (DEFAULT)" if i == sd.default.device[0] else ""
        print(f"{i}: {device['name']}{default}")
        print(f"   Channels: {device['max_input_channels']}, Sample Rate: {device['default_samplerate']}")

print("\n" + "="*60)
print("Testing microphone input...")
print("Speak now for 5 seconds...")
print("="*60 + "\n")

# Record audio
duration = 5
sample_rate = 16000

audio_data = sd.rec(
    int(duration * sample_rate),
    samplerate=sample_rate,
    channels=1,
    dtype=np.float32
)

# Show live volume meter
for i in range(duration):
    time.sleep(1)
    # Get current audio level
    current_chunk = audio_data[i*sample_rate:(i+1)*sample_rate]
    if len(current_chunk) > 0:
        volume = np.abs(current_chunk).mean()
        bars = int(volume * 100)
        print(f"Second {i+1}: {'|' * bars} ({volume:.4f})")

sd.wait()

# Analyze the recording
print("\n" + "="*60)
print("Analysis:")
print("="*60)

volume_mean = np.abs(audio_data).mean()
volume_max = np.abs(audio_data).max()
volume_std = np.abs(audio_data).std()

print(f"Average volume: {volume_mean:.6f}")
print(f"Max volume: {volume_max:.6f}")
print(f"Std deviation: {volume_std:.6f}")

if volume_mean < 0.001:
    print("\n[WARNING] Volume is VERY LOW!")
    print("Possible issues:")
    print("  1. Microphone is muted")
    print("  2. Wrong microphone selected")
    print("  3. Microphone permissions not granted")
    print("\nSolutions:")
    print("  - Check Windows Sound Settings")
    print("  - Increase microphone volume")
    print("  - Grant microphone permissions to Python")
elif volume_mean < 0.01:
    print("\n[WARNING] Volume is LOW")
    print("  - Try speaking louder or closer to the mic")
    print("  - Increase microphone boost in Windows settings")
else:
    print("\n[OK] Volume levels look good!")
    print("  - Whisper should be able to transcribe this")

# Save the recording for manual inspection
import wave
output_file = "test_recording.wav"
with wave.open(output_file, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sample_rate)
    # Convert float32 to int16
    audio_int16 = (audio_data * 32767).astype(np.int16)
    wf.writeframes(audio_int16.tobytes())

print(f"\n[SAVED] Recording saved to: {output_file}")
print("  - You can play this file to hear what was recorded")

print("\n" + "="*60)
print("Diagnostic complete!")
print("="*60 + "\n")
