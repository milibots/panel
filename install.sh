#!/bin/bash
set -e

REPO_URL="https://github.com/milibotss-spec/panel.git"
APP_DIR="$PWD/milibots-panel"
SERVICE_NAME="milibots-panel.service"
PYTHON_BIN="python3"

echo "⚙️ Starting Milibots Panel installation..."
sleep 1

# Install system dependencies
echo "📦 Installing dependencies..."
apt-get update -y >/dev/null
apt-get install -y $PYTHON_BIN python3-venv git curl >/dev/null

# Prompt for configuration
echo ""
read -p "🌐 Enter the port to run the panel on (default: 7878): " PANEL_PORT
PANEL_PORT=${PANEL_PORT:-7878}

read -p "👤 Enter admin username (default: milibots): " ADMIN_USERNAME
ADMIN_USERNAME=${ADMIN_USERNAME:-milibots}

read -sp "🔑 Enter admin password (default: milibots): " ADMIN_PASSWORD
ADMIN_PASSWORD=${ADMIN_PASSWORD:-milibots}
echo ""

# Remove any old installation
if [ -d "$APP_DIR" ]; then
    echo "🧹 Removing old installation..."
    rm -rf "$APP_DIR"
fi

# Clone repo (no GitHub auth prompt)
echo "📂 Cloning repository..."
git clone --depth 1 "$REPO_URL" "$APP_DIR"

cd "$APP_DIR"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    $PYTHON_BIN -m venv venv
fi

# Install requirements
echo "📥 Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt >/dev/null
deactivate

# Create .env file
echo "🧾 Generating .env file..."
cat <<EOF > .env
SECRET_KEY=$(openssl rand -hex 16)
ADMIN_USERNAME=${ADMIN_USERNAME}
ADMIN_PASSWORD=${ADMIN_PASSWORD}
PORT=${PANEL_PORT}
EOF

# Create systemd service
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"

echo "🧩 Creating systemd service: $SERVICE_NAME"
cat <<EOF > "$SERVICE_PATH"
[Unit]
Description=Milibots Panel Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/gunicorn -w 2 -b 0.0.0.0:${PANEL_PORT} app:app
Restart=always
EnvironmentFile=$APP_DIR/.env

[Install]
WantedBy=multi-user.target
EOF

# Reload and start service
echo "🔄 Enabling and starting service..."
systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME"

echo ""
echo "✅ Installation complete!"
echo "🌐 Your panel is live at: http://$(hostname -I | awk '{print $1}'):${PANEL_PORT}"
echo "👤 Username: ${ADMIN_USERNAME}"
echo "🔑 Password: ${ADMIN_PASSWORD}"
echo ""
