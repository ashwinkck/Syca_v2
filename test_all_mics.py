"""
Test all available microphones to find which one works
"""

import sounddevice as sd
import numpy as np
import time

print("\n" + "="*60)
print("  Testing All Microphones")
print("="*60 + "\n")

# Get all input devices
devices = sd.query_devices()
input_devices = [(i, dev) for i, dev in enumerate(devices) if dev['max_input_channels'] > 0]

print(f"Found {len(input_devices)} input devices\n")

for device_id, device in input_devices:
    print(f"\nTesting Device {device_id}: {device['name']}")
    print("-" * 60)
    
    try:
        # Record 2 seconds
        duration = 2
        sample_rate = int(device['default_samplerate'])
        
        print(f"Recording for {duration} seconds... SPEAK NOW!")
        
        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype=np.float32,
            device=device_id
        )
        sd.wait()
        
        # Analyze
        volume = np.abs(audio).mean()
        max_vol = np.abs(audio).max()
        
        print(f"Average volume: {volume:.6f}")
        print(f"Max volume: {max_vol:.6f}")
        
        if volume > 0.01:
            print("[OK] This microphone is WORKING!")
            print(f">>> USE DEVICE {device_id} <<<")
        elif volume > 0.001:
            print("[WARN] Low volume - might work with boost")
        else:
            print("[FAIL] No audio detected")
            
    except Exception as e:
        print(f"[ERROR] Failed to test: {e}")

print("\n" + "="*60)
print("Test complete!")
print("="*60 + "\n")
