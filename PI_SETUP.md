# Raspberry Pi Setup Guide for Ava Robot

## 🎯 Goal
Set up your Raspberry Pi 3B as a sensor client that streams camera + microphone to your PC for AI processing.

---

## 📋 Prerequisites

### Hardware
- Raspberry Pi 3B (or newer)
- USB Camera or Pi Camera Module
- USB Microphone or 3.5mm mic
- USB Speaker or 3.5mm speaker
- MicroSD card (16GB+) with Raspberry Pi OS
- Power supply
- WiFi connection (same network as PC)

### Software
- Raspberry Pi OS (Bullseye or newer)
- Python 3.7+

---

## 🔧 Step-by-Step Setup

### 1. Find Your PC's IP Address

**On your PC (Windows):**
```powershell
ipconfig
```
Look for "IPv4 Address" under your WiFi adapter (e.g., `192.168.1.100`)

**Write it down:** `_____._____._____._____ `

---

### 2. Copy `pi_client.py` to Raspberry Pi

**Option A: USB Drive**
1. Copy `pi_client.py` to USB drive
2. Insert USB into Pi
3. Copy to Pi home directory:
   ```bash
   cp /media/pi/USB/pi_client.py ~/
   ```

**Option B: SCP (if SSH enabled)**
```bash
# On PC:
scp pi_client.py pi@raspberrypi.local:~/
```

**Option C: Manual (Type it in)**
```bash
# On Pi:
nano ~/pi_client.py
# Paste the code, then Ctrl+X, Y, Enter
```

---

### 3. Install Dependencies on Pi

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3-pip python3-opencv portaudio19-dev

# Install Python packages
pip3 install opencv-python sounddevice websocket-client requests numpy

# Test camera
vcgencmd get_camera
# Should show: supported=1 detected=1

# Test microphone
arecord -l
# Should list your microphone

# Test speaker
speaker-test -t wav -c 2
# Press Ctrl+C to stop
```

---

### 4. Configure Audio (Important!)

```bash
# Set default audio device
sudo raspi-config
# Navigate to: System Options → Audio → Select your output device

# Test audio output
speaker-test -t wav -c 2 -D plughw:0,0
```

---

### 5. Run the Pi Client

```bash
# Replace 192.168.1.100 with YOUR PC's IP address
python3 ~/pi_client.py --server http://192.168.1.100:8000
```

**Expected Output:**
```
📷 Initializing camera...
✅ Camera ready
🎤 Initializing audio...
✅ Audio ready
🔌 Connecting to ws://192.168.1.100:8000/audio/stream...
✅ WebSocket connected
📹 Starting video stream...
🎤 Starting audio stream...
✅ Audio streaming active
```

---

## 🖥️ PC Server Setup

### 1. Install Server Dependencies

```powershell
# Activate conda environment
conda activate tf_env

# Install FastAPI and WebSocket support
pip install fastapi uvicorn websockets
```

### 2. Run PC Server

```powershell
# In Syca_v2 directory
python pc_server.py
```

**Expected Output:**
```
🤖 Ava PC Server
✅ Server initialized
🚀 Starting Ava PC Server
Server will run on: http://0.0.0.0:8000
Waiting for Pi client to connect...
```

---

## 🧪 Testing

### Test 1: Connection
1. Start PC server first
2. Start Pi client
3. You should see "🔌 Pi connected via WebSocket" on PC

### Test 2: Video
- Pi should print "📹 Sent X frames" every 5 seconds
- PC should print "👁️ Vision: ..." when analyzing frames

### Test 3: Audio
- Speak into Pi microphone
- PC should print "👤 User: [your speech]"
- PC should print "🤖 Ava: [response]"
- Pi should play audio response

---

## 🔧 Troubleshooting

### Camera Not Working
```bash
# Enable camera
sudo raspi-config
# Interface Options → Camera → Enable

# Reboot
sudo reboot
```

### Microphone Not Detected
```bash
# List audio devices
arecord -l

# Test recording
arecord -d 5 test.wav
aplay test.wav
```

### Connection Failed
```bash
# Check network
ping 192.168.1.100  # Your PC IP

# Check firewall on PC
# Windows: Allow port 8000 in Windows Firewall
```

### Audio Playback Issues
```bash
# Check volume
alsamixer
# Press F6 to select sound card, adjust volume

# Test speaker
speaker-test -t wav -c 2
```

---

## 📊 Performance Tips

### Reduce Latency
- Use Ethernet instead of WiFi
- Close other apps on Pi
- Reduce video quality if needed (edit `pi_client.py` line 44)

### Save Bandwidth
- Lower FPS (edit `pi_client.py` line 109: `time.sleep(0.2)` → `time.sleep(0.5)`)
- Reduce JPEG quality (edit `pi_client.py` line 100: `80` → `60`)

---

## 🛑 Stopping the System

### On Pi:
```bash
Ctrl+C
```

### On PC:
```bash
Ctrl+C
```

---

## 🔄 Auto-Start on Boot (Optional)

```bash
# Create systemd service
sudo nano /etc/systemd/system/ava-client.service
```

Paste:
```ini
[Unit]
Description=Ava Pi Client
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
ExecStart=/usr/bin/python3 /home/pi/pi_client.py --server http://192.168.1.100:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable ava-client
sudo systemctl start ava-client

# Check status
sudo systemctl status ava-client
```

---

## ✅ Success Checklist

- [ ] Pi connects to PC server
- [ ] Video streams from Pi to PC
- [ ] Audio streams from Pi to PC
- [ ] Speech is transcribed on PC
- [ ] Responses play on Pi speaker
- [ ] Latency < 500ms

---

## 📞 Need Help?

Check the logs:
```bash
# On Pi:
python3 pi_client.py --server http://YOUR_PC_IP:8000 2>&1 | tee pi_client.log

# On PC:
python pc_server.py 2>&1 | tee pc_server.log
```
