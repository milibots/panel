#!/bin/bash
set -e

REPO_URL="https://github.com/milibots/panel.git"
APP_DIR="$PWD/milibots-panel"
SERVICE_NAME="milibots-panel.service"
TELEGRAM_SCRIPT="/usr/local/bin/ssh-login-notify.sh"

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

# Check for Telegram configuration in existing .env
if [ -f ".env" ]; then
    TELEGRAM_BOT_TOKEN=$(grep TELEGRAM_BOT_TOKEN .env | cut -d '=' -f2)
    TELEGRAM_USER_ID=$(grep TELEGRAM_USER_ID .env | cut -d '=' -f2)
fi

# If Telegram config doesn't exist, ask user
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_USER_ID" ]; then
    echo ""
    echo "🔔 Telegram SSH Login Notifications Setup"
    echo "=========================================="
    read -p "🤖 Enter Telegram Bot Token (or press Enter to skip): " TELEGRAM_BOT_TOKEN
    read -p "👤 Enter Your Telegram User ID (or press Enter to skip): " TELEGRAM_USER_ID
    
    # Update .env file with Telegram config
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_USER_ID" ]; then
        echo "📝 Adding Telegram configuration to .env..."
        if grep -q "TELEGRAM_BOT_TOKEN" .env; then
            sed -i "s|TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}|" .env
            sed -i "s|TELEGRAM_USER_ID=.*|TELEGRAM_USER_ID=${TELEGRAM_USER_ID}|" .env
        else
            echo "TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}" >> .env
            echo "TELEGRAM_USER_ID=${TELEGRAM_USER_ID}" >> .env
        fi
        
        # Create/update Telegram notification script
        echo "🔔 Creating SSH login notification script..."
        cat <<EOF > $TELEGRAM_SCRIPT
#!/bin/bash

# Telegram Bot Configuration
BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
USER_ID="$TELEGRAM_USER_ID"

# Get server information
SERVER_IP=\$(curl -s https://ipapi.co/ip/ || hostname -I | awk '{print \$1}')
SERVER_NAME=\$(hostname)

# Login information
LOGIN_USER=\$PAM_USER
LOGIN_TYPE=\$PAM_TYPE
REMOTE_IP=\${PAM_RHOST:-"unknown"}
LOGIN_TIME=\$(date '+%Y-%m-%d %H:%M:%S')

if [ "\$PAM_TYPE" = "open_session" ]; then
    MESSAGE="🔐 *SSH Login Alert* 🔐

🖥️ *Server:* \${SERVER_NAME}
🌐 *IP:* \${SERVER_IP}
👤 *User:* \${LOGIN_USER}
📍 *From IP:* \${REMOTE_IP}
🕐 *Time:* \${LOGIN_TIME}
🔍 *Status:* Login Successful"

    # Send to Telegram
    curl -s -X POST "https://api.telegram.org/bot\${BOT_TOKEN}/sendMessage" \\
        -d chat_id="\${USER_ID}" \\
        -d text="\${MESSAGE}" \\
        -d parse_mode="Markdown" > /dev/null 2>&1
fi

exit 0
EOF

        # Make the script executable
        chmod +x $TELEGRAM_SCRIPT

        # Configure PAM to trigger the script on SSH login
        echo "🔧 Configuring PAM for SSH notifications..."
        if [ ! -f /etc/pam.d/sshd ]; then
            echo "❌ PAM SSH configuration not found!"
        else
            # Remove any existing configuration
            sed -i '/ssh-login-notify/d' /etc/pam.d/sshd
            # Add new configuration
            echo "session optional pam_exec.so /usr/local/bin/ssh-login-notify.sh" >> /etc/pam.d/sshd
            echo "✅ PAM configured for SSH notifications"
        fi

        # Test Telegram configuration
        echo "🧪 Testing Telegram configuration..."
        TEST_MESSAGE="✅ *SSH Notification Test* ✅

🤖 Bot is configured successfully!
🖥️ Server: \$(hostname)
🌐 IP: \$(curl -s https://ipapi.co/ip/ || echo "unknown")
🕐 Time: \$(date '+%Y-%m-%d %H:%M:%S')

You will receive this notification whenever someone logs in via SSH."

        TEST_RESULT=$(curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d chat_id="${TELEGRAM_USER_ID}" \
            -d text="${TEST_MESSAGE}" \
            -d parse_mode="Markdown" | grep -q '"ok":true' && echo "success" || echo "failed")

        if [ "$TEST_RESULT" = "success" ]; then
            echo "✅ Telegram test notification sent successfully!"
        else
            echo "❌ Failed to send Telegram test notification"
            echo "💡 Please check your Bot Token and User ID"
        fi
    else
        echo "ℹ️ Telegram notifications skipped."
    fi
else
    echo "ℹ️ Telegram configuration already exists."
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

# Wait a moment for service to start
sleep 2

# Check service status
SERVICE_STATUS=$(systemctl is-active $SERVICE_NAME)
if [ "$SERVICE_STATUS" = "active" ]; then
    echo "✅ Service started successfully!"
else
    echo "❌ Service failed to start. Check status with: systemctl status $SERVICE_NAME"
fi

# Detect server IP using ipapi
echo "🌍 Detecting server IP..."
SERVER_IP=$(curl -s https://ipapi.co/ip/ || echo "127.0.0.1")

# Get PORT from .env file or use default
PORT=$(grep PORT .env 2>/dev/null | cut -d '=' -f2)
PORT=${PORT:-7878}

echo ""
echo "✅ Milibots Panel updated successfully!"
echo "🌐 URL: http://${SERVER_IP}:${PORT}"
echo ""

# Show Telegram status
if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_USER_ID" ]; then
    echo "🔔 SSH Login Notifications: ✅ Enabled"
    echo "   You will receive Telegram alerts for SSH logins"
else
    echo "🔔 SSH Login Notifications: ❌ Disabled"
fi

echo ""
echo "🔧 Management commands:"
echo "   systemctl status $SERVICE_NAME    # Check service status"
echo "   journalctl -u $SERVICE_NAME -f   # View logs"
echo "   systemctl restart $SERVICE_NAME   # Restart service"
