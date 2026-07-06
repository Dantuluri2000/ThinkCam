#!/bin/bash
# ThinkCam Home Setup Script
# Run this on any home device (Linux/Mac/Raspberry Pi/WSL)
# Usage: bash setup-home.sh

set -e

echo "=== ThinkCam Home Setup ==="

# 1. Check Docker
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "Docker installed. You may need to log out and back in."
fi

# 2. Create credentials file
if [ ! -f wyze.env ]; then
    echo ""
    echo "Creating wyze.env credentials file..."
    cat > wyze.env << 'ENVEOF'
WYZE_EMAIL=sridhar.dantuluri@gmail.com
WYZE_PASSWORD=qg6,.Cn-p8LVhac
API_ID=06310c1e-1115-4122-814d-209f3b17d742
API_KEY=WPwnoZ0e1tQlMvZ6XDgesVkUl9wzOX0AkOHSdxCjYC1V0VbJSYPDSrsWUHvs
WB_AUTH=false
ENABLE_AUDIO=false
ON_DEMAND=false
ENVEOF
    echo "wyze.env created."
fi

# 3. Create local env
if [ ! -f .env.local ]; then
    cat > .env.local << 'LOCALEOF'
WYZE_EMAIL=sridhar.dantuluri@gmail.com
WYZE_PASSWORD=qg6,.Cn-p8LVhac
WYZE_KEY_ID=06310c1e-1115-4122-814d-209f3b17d742
WYZE_API_KEY=WPwnoZ0e1tQlMvZ6XDgesVkUl9wzOX0AkOHSdxCjYC1V0VbJSYPDSrsWUHvs
WYZE_RTSP_URL=rtsp://localhost:8554/front-porch-cam
WYZE_MOCK=false
ONEDRIVE_MOCK=true
FIREBASE_MOCK=true
LOCALEOF
fi

# 4. Start Wyze Bridge
echo ""
echo "Starting Wyze Bridge (connects to your camera)..."
mkdir -p wyze-storage
docker rm -f wyze-bridge-thinkcam 2>/dev/null || true
docker run -d \
  --name wyze-bridge-thinkcam \
  --restart unless-stopped \
  -p 8554:8554 \
  -p 5050:5000 \
  -v "$(pwd)/wyze-storage:/tokens" \
  --env-file wyze.env \
  mrlt8/wyze-bridge:latest

echo "Waiting 30s for camera to connect..."
sleep 30
docker logs wyze-bridge-thinkcam 2>&1 | tail -10

# 5. Set up Python
echo ""
echo "Setting up Python environment..."
python3 -m venv venv
./venv/bin/pip install --upgrade pip setuptools wheel -q
./venv/bin/pip install -r requirements.txt -q

# 6. Start ThinkCam backend
echo ""
echo "Starting ThinkCam backend..."
PYTHONUTF8=1 ./venv/bin/python main.py &
BACKEND_PID=$!
sleep 5

# 7. Verify
echo ""
echo "=== Setup Complete ==="
echo "Wyze Bridge UI:  http://localhost:5050"
echo "ThinkCam API:    http://localhost:8000"
echo "Health check:    http://localhost:8000/health"
echo ""
curl -s http://localhost:8000/health 2>/dev/null || echo "Backend starting..."
