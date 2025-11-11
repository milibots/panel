# MiliBots Panel 🛠️

A lightweight Flask-based admin panel with automatic systemd service setup.

---

## 🚀 Quick Install

Run this on any **Ubuntu/Debian** server (as root or with sudo):

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/milibots/panel/main/install.sh)
````

The installer will:

* Ask for your desired **port**, **admin username**, and **password**
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

## 🧹 Uninstall

To completely remove the panel and its service:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/milibots/panel/main/uninstall.sh)
```

This will:

* Stop and disable the systemd service
* Remove the service file
* Delete the project folder and virtual environment

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

## 📦 Tech Stack

* **Flask** — web framework
* **Gunicorn** — WSGI server
* **Systemd** — for background service management
* **Python venv** — isolated environment

---

## 🧑‍💻 Maintainer

Developed by **MiliBots Team**
GitHub: [@milibots](https://github.com/milibots)


Do you want me to do that next?
```

