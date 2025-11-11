from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, jsonify
import os
import subprocess
import shlex
import time
import psutil
from dotenv import load_dotenv
from flask_socketio import SocketIO
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'a_default_secret_key_please_change_me')
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=60, ping_interval=25)

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

service_states = {}

def run_cmd(cmd, timeout=10):
    try:
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=timeout)
        return (result.returncode == 0), result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", f"Command error: {e}"

def get_service_status(service_name):
    ok, output, err = run_cmd(f"systemctl is-active {shlex.quote(service_name)}")
    active_status = output.strip() if ok else "unknown"
    
    ok, output, err = run_cmd(f"systemctl is-enabled {shlex.quote(service_name)}")
    enabled_status = output.strip() if ok else "unknown"
    
    return active_status, enabled_status

def update_all_service_states():
    services, error = get_running_services()
    if not error:
        for service in services:
            service_name = service['unit']
            active_status, enabled_status = get_service_status(service_name)
            service_states[service_name] = {
                'active': service['active'],
                'enabled': enabled_status,
                'description': service['description']
            }
        socketio.emit('service_states_update', service_states)

def get_system_stats():
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        load_avg = os.getloadavg()
        
        return {
            'cpu_percent': cpu_percent,
            'memory_total': memory.total,
            'memory_used': memory.used,
            'memory_percent': memory.percent,
            'disk_total': disk.total,
            'disk_used': disk.used,
            'disk_percent': disk.percent,
            'load_avg': load_avg,
            'uptime': time.time() - psutil.boot_time()
        }
    except Exception as e:
        return {'error': str(e)}

def run_systemctl_command(action, service_name):
    valid_actions = ['start', 'stop', 'restart', 'status', 'enable', 'disable', 'delete']
    if action not in valid_actions:
        return False, f"Invalid action: {action}"

    service_path = shlex.quote(service_name)

    try:
        if action == 'delete':
            run_cmd(f"sudo systemctl stop {service_path}")
            run_cmd(f"sudo systemctl disable {service_path}")
            ok, _, _ = run_cmd(f"sudo rm -f /etc/systemd/system/{service_path}")
            if ok:
                run_cmd("sudo systemctl daemon-reload")
                return True, f"Service '{service_name}' deleted successfully."
            return False, f"Failed to delete service '{service_name}'"

        if action in ['enable', 'disable']:
            ok, out, err = run_cmd(f"sudo systemctl {action} {service_path}")
            if ok:
                run_cmd("sudo systemctl daemon-reload")
                return True, out or f"Service '{service_name}' {action}d successfully."
            return False, err or out

        if action == 'restart':
            ok1, _, err1 = run_cmd(f"sudo systemctl stop {service_path}")
            time.sleep(2)

            ok2, pid_out, _ = run_cmd(f"systemctl show -p MainPID {service_path} | cut -d= -f2")
            if pid_out.strip() and pid_out.strip() != "0":
                run_cmd(f"sudo kill -9 {pid_out.strip()}")

            if service_name == 'bot.service':
                run_cmd("sudo tmux kill-session -t bot 2>/dev/null")
                run_cmd("sudo rm -f /root/NIVa/bot/NIVA.session /root/NIVa/bot/NIVA.session-journal")

            ok3, _, err3 = run_cmd(f"sudo systemctl start {service_path}")
            if ok1 and ok3:
                return True, f"Service '{service_name}' restarted successfully."
            return False, f"Restart failed: {err1 or err3}"

        ok, out, err = run_cmd(f"sudo systemctl {action} {service_path}")
        if not ok:
            if action == 'stop':
                ok_pid, pid_out, _ = run_cmd(f"systemctl show -p MainPID {service_path} | cut -d= -f2")
                if ok_pid and pid_out.strip() and pid_out.strip() != "0":
                    run_cmd(f"sudo kill -9 {pid_out.strip()}")
            return ok, err or out

        return True, out or f"Service '{service_name}' {action}ed successfully."

    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def get_running_services():
    ok, output, err = run_cmd("systemctl list-units --type=service --all --no-pager --no-legend")
    if not ok:
        return [], f"Failed to fetch service list: {err}"

    services = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 5:
            unit = parts[0]
            if not unit.endswith(".service"):
                continue
            services.append({
                'unit': unit,
                'load': parts[1],
                'active': parts[2],
                'sub': parts[3],
                'description': ' '.join(parts[4:])
            })
    return services, None

def stream_service_logs(service_name):
    command = f"sudo journalctl -u {shlex.quote(service_name)} -f -n 50"
    try:
        process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

        def generate():
            try:
                for line in iter(process.stdout.readline, ''):
                    yield f"data: {line.strip()}\n\n"
            except Exception as e:
                yield f"data: ERROR: {str(e)}\n\n"
            finally:
                process.terminate()

        return generate(), None

    except FileNotFoundError:
        return None, "Error: 'journalctl' not found."
    except Exception as e:
        return None, f"Error streaming logs: {e}"

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
    socketio.emit('service_states_update', service_states)

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

@socketio.on('request_service_update')
def handle_service_update():
    update_all_service_states()

@socketio.on('request_system_stats')
def handle_system_stats():
    stats = get_system_stats()
    socketio.emit('system_stats_update', stats)

@app.route('/')
def index():
    if session.get('logged_in'):
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('✅ Logged in successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('❌ Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('👋 You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/admin')
def admin_dashboard():
    if not session.get('logged_in'):
        flash('⚠️ Please log in to access the admin dashboard.', 'warning')
        return redirect(url_for('login'))

    services, error = get_running_services()
    if error:
        flash(error, 'danger')
        services = []
    
    update_all_service_states()
    
    return render_template('admin.html', services=services)

@app.route('/admin/service/<service_name>', methods=['POST'])
def admin_service_action(service_name):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Please log in first.'}), 401

    action = request.form.get('action')
    if not action:
        return jsonify({'success': False, 'message': 'No action specified.'}), 400

    success, message = run_systemctl_command(action, service_name)
    
    update_all_service_states()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': success, 'message': message})
    else:
        flash(message, 'success' if success else 'danger')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/service/<service_name>/status')
def admin_service_status(service_name):
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    active_status, enabled_status = get_service_status(service_name)
    return jsonify({
        'service': service_name,
        'active': active_status,
        'enabled': enabled_status
    })

@app.route('/admin/logs/<service_name>')
def admin_service_logs(service_name):
    if not session.get('logged_in'):
        flash('⚠️ Please log in to view logs.', 'warning')
        return redirect(url_for('login'))

    generator, error = stream_service_logs(service_name)
    if error:
        flash(error, 'danger')
        return redirect(url_for('admin_dashboard'))

    return Response(generator, mimetype='text/event-stream')

@app.route('/admin/system-stats')
def admin_system_stats():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    stats = get_system_stats()
    return jsonify(stats)

if __name__ == '__main__':
    print("✅ Flask Admin Service Panel running on http://0.0.0.0:7878")
    socketio.run(app, debug=True, host='0.0.0.0', port=7878, allow_unsafe_werkzeug=True)
