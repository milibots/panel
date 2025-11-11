#!/bin/bash
set -e

REPO_URL="https://github.com/GeeksOfbenz/milibots-panel.git"
APP_DIR="/opt/milibots-panel"

echo "📦 Installing dependencies..."
sudo apt update -y
sudo apt install -y python3 python3-venv python3-pip git systemd curl

echo "📂 Cloning repository..."
if [ -d "$APP_DIR" ]; then
    echo "🔄 Existing installation found, pulling latest changes..."
    cd "$APP_DIR"
    sudo git pull
else
    sudo git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi

echo "⚙️ Running setup..."
sudo python3 setup.py

echo "✅ Installation completed successfully!"
echo ""
echo "🌐 Your app should now be live on port 7878."
echo "👉 Check logs using: sudo journalctl -u milibots-panel.service -f"
