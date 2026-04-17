import os
import io
import subprocess
import threading
import time
import ctypes
import sys
from datetime import datetime
from functools import wraps

from flask import Flask, session, request, render_template_string, send_file, jsonify, redirect, url_for
from PIL import ImageGrab

# ==================== CONFIGURATION ====================
USERS = {
    "admin": "password123",
    "user1": "userpass",
    "tech": "tech123"
}
SCREEN_REFRESH_INTERVAL = 0.2  # seconds (200ms)
PORT = 6767
HOST = "0.0.0.0"
# =======================================================

app = Flask(__name__)
app.secret_key = os.urandom(24)

current_frame = None
frame_lock = threading.Lock()

def capture_screen():
    global current_frame
    while True:
        try:
            screenshot = ImageGrab.grab()
            with io.BytesIO() as output:
                screenshot.save(output, format="JPEG", quality=60, optimize=True)
                with frame_lock:
                    current_frame = output.getvalue()
        except Exception as e:
            print(f"Screen capture error: {e}")
        time.sleep(SCREEN_REFRESH_INTERVAL)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ==================== ROUTES ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in USERS and USERS[username] == password:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template_string(LOGIN_TEMPLATE, error="Invalid credentials")
    return render_template_string(LOGIN_TEMPLATE, error=None)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    return render_template_string(DASHBOARD_TEMPLATE)

@app.route('/screen.jpg')
@login_required
def serve_screen():
    with frame_lock:
        if current_frame is None:
            blank = ImageGrab.grab()
            with io.BytesIO() as out:
                blank.save(out, format="JPEG")
                img_data = out.getvalue()
        else:
            img_data = current_frame
    return send_file(io.BytesIO(img_data), mimetype='image/jpeg')

@app.route('/api/command', methods=['POST'])
@login_required
def execute_command():
    data = request.get_json()
    cmd = data.get('cmd', '').strip()
    if not cmd:
        return jsonify({'output': '', 'error': 'No command provided'})
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            encoding='utf-8',
            errors='replace'
        )
        output = result.stdout + result.stderr
        if not output:
            output = "[Command executed with no output]"
        return jsonify({'output': output, 'error': None})
    except subprocess.TimeoutExpired:
        return jsonify({'output': '', 'error': 'Command timed out (30s)'})
    except Exception as e:
        return jsonify({'output': '', 'error': str(e)})

# ==================== HTML TEMPLATES ====================
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Remote Control - Login</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1e1e2f; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-card { background: #2d2d3a; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); width: 300px; }
        h2 { color: #fff; text-align: center; margin-bottom: 1.5rem; }
        input { width: 100%; padding: 10px; margin: 8px 0; border: none; border-radius: 4px; background: #3d3d4a; color: #fff; }
        button { width: 100%; padding: 10px; background: #4caf50; border: none; border-radius: 4px; color: white; font-weight: bold; cursor: pointer; }
        button:hover { background: #45a049; }
        .error { color: #ff6b6b; text-align: center; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>Remote Access Login</h2>
        <form method="post">
            <input type="text" name="username" placeholder="Username" required autofocus>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
            {% if error %}
                <div class="error">{{ error }}</div>
            {% endif %}
        </form>
    </div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Remote Control Dashboard</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #0a0a0a; color: #eee; }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { margin-top: 0; color: #4caf50; }
        .logout-btn { float: right; background: #f44336; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; }
        .logout-btn:hover { background: #d32f2f; }
        .status { background: #2d2d2d; padding: 10px; border-radius: 4px; margin-bottom: 20px; font-size: 0.9rem; }
        .screen-section { margin-bottom: 30px; }
        .screen-section h2 { margin-bottom: 10px; }
        .screen-container { background: #000; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.5); text-align: center; }
        #screen { width: 100%; max-height: 70vh; object-fit: contain; background: black; }
        .controls { margin-top: 10px; display: flex; gap: 10px; justify-content: center; }
        button { background: #3a3a3a; border: none; color: white; padding: 6px 12px; border-radius: 4px; cursor: pointer; }
        button:hover { background: #5a5a5a; }
        .terminal-section { background: #1e1e1e; border-radius: 8px; padding: 15px; margin-top: 20px; }
        .terminal-output { background: #0c0c0c; border: 1px solid #333; height: 300px; overflow-y: auto; font-family: monospace; padding: 10px; border-radius: 4px; white-space: pre-wrap; }
        .command-line { display: flex; gap: 10px; margin-top: 10px; }
        #cmdInput { flex: 1; background: #2d2d2d; border: 1px solid #555; color: #0f0; padding: 10px; font-family: monospace; border-radius: 4px; }
        #sendCmd { background: #4caf50; }
        #sendCmd:hover { background: #45a049; }
        .error-text { color: #ff6b6b; }
        hr { border-color: #333; margin: 20px 0; }
    </style>
</head>
<body>
<div class="container">
    <div style="overflow: auto;">
        <h1>🖥️ Remote Control Panel</h1>
        <a href="/logout" class="logout-btn">Logout</a>
    </div>
    <div class="status">
        Logged in as: <strong>{{ session.username }}</strong> | Host: <span id="hostname">loading...</span>
    </div>

    <div class="screen-section">
        <h2>📺 Live Screen Capture</h2>
        <div class="screen-container">
            <img id="screen" src="/screen.jpg" alt="Screen stream">
        </div>
        <div class="controls">
            <button id="refreshBtn">🔄 Refresh Now</button>
            <span style="font-size: 0.8rem;">Auto-updates every 200ms</span>
        </div>
    </div>

    <div class="terminal-section">
        <h2>⌨️ Command Prompt (Full System Control)</h2>
        <div class="terminal-output" id="terminalOutput">
            <span style="color:#888;">> Ready. Enter a command (e.g., dir, ipconfig, notepad)</span>
        </div>
        <div class="command-line">
            <input type="text" id="cmdInput" placeholder="Type command here..." autofocus>
            <button id="sendCmd">Execute</button>
        </div>
    </div>
</div>

<script>
    const screenImg = document.getElementById('screen');
    const terminalOutput = document.getElementById('terminalOutput');
    const cmdInput = document.getElementById('cmdInput');
    const sendBtn = document.getElementById('sendCmd');

    function updateScreen() {
        const timestamp = new Date().getTime();
        screenImg.src = '/screen.jpg?t=' + timestamp;
    }

    let screenInterval = setInterval(updateScreen, 200);

    document.getElementById('refreshBtn').addEventListener('click', () => {
        updateScreen();
    });

    function appendToTerminal(text, isError = false) {
        const line = document.createElement('div');
        line.textContent = text;
        if (isError) line.style.color = '#ff6b6b';
        else line.style.color = '#0f0';
        terminalOutput.appendChild(line);
        terminalOutput.scrollTop = terminalOutput.scrollHeight;
    }

    async function executeCommand(cmd) {
        if (!cmd.trim()) return;
        appendToTerminal(`> ${cmd}`, false);
        cmdInput.value = '';
        try {
            const response = await fetch('/api/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cmd: cmd })
            });
            const data = await response.json();
            if (data.error) {
                appendToTerminal(`[ERROR] ${data.error}`, true);
            } else {
                if (data.output) {
                    const lines = data.output.split('\\n');
                    for (let line of lines) {
                        if (line.trim()) appendToTerminal(line, false);
                    }
                } else {
                    appendToTerminal('[Command completed with no output]', false);
                }
            }
        } catch (err) {
            appendToTerminal(`[NETWORK ERROR] ${err.message}`, true);
        }
        appendToTerminal('---', false);
    }

    sendBtn.addEventListener('click', () => {
        executeCommand(cmdInput.value);
    });
    cmdInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') executeCommand(cmdInput.value);
    });

    fetch('/api/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cmd: 'hostname' })
    })
    .then(r => r.json())
    .then(data => {
        if (data.output) document.getElementById('hostname').innerText = data.output.trim();
        else document.getElementById('hostname').innerText = 'unknown';
    })
    .catch(() => document.getElementById('hostname').innerText = 'unknown');
</script>
</body>
</html>
"""
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, None, None, 1
    )
    sys.exit()
def add_firewall_rule():
    exe_path = sys.executable
    subprocess.run(
        f'netsh advfirewall firewall add rule name="RemoteAdmin" dir=in action=allow program="{exe_path}" enable=yes',
        shell=True
    )
def add_to_startup():
    import winreg
    import sys
    exe_path = sys.executable  # path of the running exe
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "RemoteAdmin", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        print("[+] Added to startup registry")
    except Exception as e:
        print(f"[-] Failed to add startup: {e}")

add_firewall_rule()
add_to_startup()
if __name__ == '__main__':
    capture_thread = threading.Thread(target=capture_screen, daemon=True)
    capture_thread.start()
    time.sleep(0.5)

    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print("\n" + "="*50)
    print(f"✅ Remote Administration Server Started")
    print(f"📍 Local access:   http://127.0.0.1:{PORT}")
    print(f"🌐 Network access: http://{local_ip}:{PORT}")
    print(f"👥 Available users: {', '.join(USERS.keys())}")
    print("⚠️  WARNING: Anyone on your network can attempt to login")
    print("="*50 + "\n")

    app.run(host=HOST, port=PORT, debug=False, threaded=True)