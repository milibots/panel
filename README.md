# MiliBots Panel 🛠️

A lightweight Flask-based admin panel with automatic systemd service setup and SSH login notifications.

---

## 🚀 Quick Install

Run this on any **Ubuntu/Debian** server (as root or with sudo):

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/milibots/panel/main/install.sh)
```

The installer will:

* Ask for your desired **port**, **admin username**, and **password**
* Set up **Telegram SSH login notifications** (optional)
* Automatically install Python & dependencies
* Create a `.env` file
* Set up a systemd service: `milibots-panel.service`
* Start the panel automatically

After installation, access your panel at:

```
http://<your-server-ip>:<chosen-port>
```

Default credentials (if you skip prompts):

```
Username: milibots
Password: milibots
```

---

## 🔔 Telegram SSH Notifications

During installation, you can set up **real-time Telegram notifications** for SSH logins:

1. **Create a Telegram Bot** using [@BotFather](https://t.me/botfather)
2. **Get your User ID** using [@userinfobot](https://t.me/userinfobot)
3. **Enter credentials** during installation

You'll receive instant notifications when anyone logs into your server via SSH:

```
🔐 SSH Login Alert 🔐

🖥️ Server: your-server
🌐 IP: 192.168.1.100
👤 User: root
📍 From IP: 123.456.789.0
🕐 Time: 2024-01-15 14:30:25
🔍 Status: Login Successful
```

---

## 🧹 Uninstall

To completely remove the panel and its service:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/milibots/panel/main/uninstall.sh)
```

This will:

* Stop and disable the systemd service
* Remove the service file
* Delete the project folder and virtual environment
* Remove SSH notification scripts

---

## 🔄 Update

To update your existing panel to the latest version:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/milibots/panel/main/update.sh)
```

This will:

* Stop the running service
* Pull the latest version from GitHub
* Update dependencies
* Set up Telegram notifications (if not already configured)
* Restart the panel automatically

---

## ⚙️ Service Management

You can manage the systemd service manually using:

```bash
systemctl status milibots-panel.service
systemctl restart milibots-panel.service
systemctl stop milibots-panel.service
```

---

## 🛡️ Features

### Admin Panel
- **Service Management** - Start, stop, restart systemd services
- **Real-time Logs** - View service logs in real-time
- **System Monitoring** - CPU, memory, disk usage statistics
- **Web-based Interface** - Easy-to-use web dashboard

### Security
- **SSH Login Alerts** - Telegram notifications for all SSH logins
- **PAM Integration** - Automatic detection of SSH sessions
- **Secure Authentication** - Protected admin interface

---

## 📦 Tech Stack

* **Flask** — web framework
* **Gunicorn** — WSGI server
* **Systemd** — for background service management
* **Python venv** — isolated environment
* **Telegram Bot API** — real-time notifications
* **PAM** — SSH login detection

---

## 🧑‍💻 Maintainer

Developed by **MiliBots Team**
GitHub: [@milibots](https://github.com/milibots)

---

## 🔧 Manual Telegram Setup

If you skipped Telegram setup during installation, you can add it later:

1. Edit your `.env` file:
```bash
nano /path/to/milibots-panel/.env
```

2. Add these lines:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_USER_ID=your_user_id_here
```

3. Restart the service:
```bash
systemctl restart milibots-panel.service
```
