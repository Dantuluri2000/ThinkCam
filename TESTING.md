# 🚀 ThinkCam Testing Guide - Step by Step

## ⏱️ Estimated Time: 15-20 minutes

---

## STEP 1: Install Dependencies

```bash
cd C:\Users\sridhard\OneDrive - Microsoft\Documents\ThinkCam

# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install Python packages
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed fastapi-0.104.1 opencv-python-4.8.1.78 mediapipe-0.10.0 ...
```

---

## STEP 2: Start Wyze Bridge (Docker)

In a **NEW terminal** (keep this running):

```bash
docker run -d \
  -p 8554:8554 \
  -p 8888:8888 \
  -p 5050:5000 \
  -e WYZE_EMAIL=your_wyze_email@gmail.com \
  -e WYZE_PASSWORD=your_wyze_password \
  -e WB_AUTH=false \
  mrlt8/wyze-bridge
```

**Replace:**
- `your_wyze_email@gmail.com` - Your actual Wyze account email
- `your_wyze_password` - Your actual Wyze password

**Wait 30-60 seconds for camera to connect**

Then check: http://localhost:5050
- You should see your Wyze Cam 4 listed
- Look for the RTSP URL (e.g., `rtsp://localhost:8554/stream/front_door`)

---

## STEP 3: Configure Credentials

Edit `.env.local` in ThinkCam folder:

```bash
# Edit the file with your values:
WYZE_KEY_ID=06310c1e-1115-4122-814d-209f3b17d742
WYZE_API_KEY=WPwnoZ0e1tQlMvZ6XDgesVkUl9wzOX0AkOHSdxCjYC1V0VbJSYPDSrsWUHvs
WYZE_EMAIL=your_wyze_email@gmail.com
WYZE_PASSWORD=your_wyze_password

WYZE_RTSP_URL=rtsp://localhost:8554/stream/front_door
WYZE_MOCK=false

ONEDRIVE_MOCK=true
FIREBASE_MOCK=true
```

**Get RTSP URL from:** http://localhost:5050 (Wyze Bridge UI)

---

## STEP 4: Create Logs Directory

```bash
cd C:\Users\sridhard\OneDrive - Microsoft\Documents\ThinkCam
mkdir logs
```

---

## STEP 5: Start ThinkCam Backend

In your first terminal (venv activated):

```bash
python main.py
```

**Expected output:**
```
🖥️  DEVICE CAPABILITIES
======================
Device Type:        windows_laptop
CPU Cores:          8
RAM:                16.0 GB
...

✅ Wyze API Key loaded (ID: 06310c1e...)
✅ RTSP stream connection attempt...
✅ Motion detection mode: mediapipe_full

🌐 Starting API server on 0.0.0.0:8000
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal open!**

---

## STEP 6: Test API Endpoints

In a **THIRD terminal**, test the API:

```bash
# Health check
curl http://localhost:8000/health

# Get device info
curl http://localhost:8000/api/device-info

# Get RTSP URL
curl http://localhost:8000/api/rtsp-url

# Get current status
curl http://localhost:8000/api/status

# Get events
curl http://localhost:8000/api/events?limit=10
```

**Expected responses:**
```json
{
  "status": "healthy",
  "device": "windows_laptop",
  "stream": "connected"
}
```

---

## STEP 7: Monitor Motion Detection

**Go to Wyze Bridge UI:** http://localhost:5050

- Move in front of your Wyze Cam 4
- Watch the backend terminal for motion alerts:
  ```
  Motion triggered! Confidence: 87%
  📹 Recording started
  ⬆️  Uploading: motion_20260706_090000_0.87.mp4
  ✅ Uploaded to OneDrive (mock)
  ```

---

## ✅ Success Criteria

- [ ] Docker Wyze Bridge running (http://localhost:5050 accessible)
- [ ] ThinkCam backend starts without errors
- [ ] `curl http://localhost:8000/health` returns "healthy"
- [ ] API endpoints respond with valid JSON
- [ ] Motion detection triggers when you move in front of camera
- [ ] Clips saved to `clips/` folder
- [ ] No Python errors in terminal

---

## 🐛 Troubleshooting

### "ConnectionError: can't connect to rtsp stream"
**Solution:**
1. Check Wyze Bridge is running: `docker ps | grep wyze-bridge`
2. Visit http://localhost:5050 to verify camera is connected
3. Get correct RTSP URL from UI
4. Update WYZE_RTSP_URL in .env.local

### "ModuleNotFoundError: No module named 'mediapipe'"
**Solution:**
```bash
pip install mediapipe
```

### "Permission denied: ./logs"
**Solution:**
```bash
mkdir logs
chmod -R 755 logs  # On macOS/Linux
# Or just create the folder in File Explorer on Windows
```

### "Firebase init failed / Firebase not initialized"
**This is OK!** We're using FIREBASE_MOCK=true for testing
- When you setup real Firebase later, just set FIREBASE_MOCK=false

### Motion detection not triggering
**Try:**
1. Increase sensitivity: `MOTION_SENSITIVITY=0.3` (lower = more sensitive)
2. Check logs: `tail -f logs/thinkcam.log`
3. Verify camera feed is live in Wyze Bridge UI

---

## 📊 What's Happening

```
1. You move in front of camera
   ↓
2. Wyze Bridge captures RTSP stream
   ↓
3. ThinkCam analyzes frames with MediaPipe
   ↓
4. Motion detected → starts recording (60 sec buffer)
   ↓
5. Frames buffered to memory
   ↓
6. Recording saved to ./clips/ (MP4 video)
   ↓
7. (Optional) Uploaded to OneDrive
   ↓
8. (Optional) Push notification sent to mobile app
```

---

## 🎯 Next After Testing

- ✅ Verify backend works
- 🔄 Check mobile app notification (when ready)
- 📱 Integrate with Android app
- ☁️ Setup real OneDrive storage
- 🔔 Setup Firebase for push alerts
- 🎬 Test end-to-end flow

---

Ready? Let's do this! 🚀
