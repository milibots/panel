#!/bin/bash
set -e

REPO_URL="https://github.com/milibotss-spec/panel.git"
APP_DIR="$PWD/milibots-panel"
SERVICE_NAME="milibots-panel.service"

echo "🔄 Updating Milibots Panel..."

# Check if service exists
if systemctl list-units --full -all | grep -Fq "$SERVICE_NAME"; then
    echo "🛑 Stopping service before update..."
    systemctl stop "$SERVICE_NAME" || true
else
    echo "⚠️ No existing systemd service found — will recreate."
fi

# If directory exists, pull updates; else clone fresh
if [ -d "$APP_DIR/.git" ]; then
    echo "📂 Existing installation found. Pulling latest changes..."
    cd "$APP_DIR"
    git reset --hard
    git pull origin main --force
else
    echo "📦 No installation found. Cloning fresh from repository..."
    rm -rf "$APP_DIR"
    git clone --depth 1 "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
fi

# Update Python dependencies
echo "📥 Installing/updating Python dependencies..."
source venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt >/dev/null
deactivate

# Recreate systemd service file if missing
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"
if [ ! -f "$SERVICE_PATH" ]; then
    echo "🧩 Creating systemd service file..."
    PORT=$(grep PORT .env | cut -d '=' -f2)
    [ -z "$PORT" ] && PORT=7878

    cat <<EOF > "$SERVICE_PATH"
[Unit]
Description=Milibots Panel Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/gunicorn -w 2 -b 0.0.0.0:${PORT} app:app
Restart=always
EnvironmentFile=$APP_DIR/.env

[Install]
WantedBy=multi-user.target
EOF
fi

# Reload systemd and restart service
echo "🚀 Restarting service..."
systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME"

echo ""
echo "✅ Milibots Panel updated successfully!"
echo "🌐 URL: http://$(hostname -I | awk '{print $1}'):${PORT}"
echo ""
