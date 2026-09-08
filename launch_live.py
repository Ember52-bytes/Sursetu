"""
PALASH Setu - 1-Click Live Public Launcher (Powered by Cloudflare Quick Tunnels)
--------------------------------------------------------------------------------
Zero Configuration, Zero Signup, No Auth Tokens Required.
Generates an official high-speed HTTPS Cloudflare link.
"""

import os
import re
import subprocess
import sys
import threading
import time
from server import app

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CLOUDFLARED_PATH = os.path.join(PROJECT_ROOT, "cloudflared.exe")
PORT = int(os.environ.get("PORT", 8000))


def run_flask():
    """Run Flask server on local port."""
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)


def start_live():
    print("\n" + "=" * 65)
    print("  🌿 PALASH SETU - STARTING CLOUDFLARE LIVE PUBLIC SERVER")
    print("=" * 65)

    if not os.path.exists(CLOUDFLARED_PATH):
        print(f"[ERROR] cloudflared.exe not found at {CLOUDFLARED_PATH}")
        sys.exit(1)

    # 1. Start Flask in background thread
    server_thread = threading.Thread(target=run_flask, daemon=True)
    server_thread.start()
    time.sleep(1.5)

    # 2. Launch cloudflared tunnel
    cmd = [CLOUDFLARED_PATH, "tunnel", "--url", f"http://127.0.0.1:{PORT}"]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace"
    )

    public_url = None
    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

    # Read output to capture the public URL
    for line in iter(process.stdout.readline, ""):
        match = url_pattern.search(line)
        if match:
            public_url = match.group(0)
            break

    if public_url:
        # Save to file for instant discovery
        with open(os.path.join(PROJECT_ROOT, "LIVE_LINK.txt"), "w", encoding="utf-8") as f:
            f.write(public_url.strip())

        print("\n" + "*" * 65, flush=True)
        print("  🎉 YOUR PALASH SETU LIVE PUBLIC LINK IS READY!", flush=True)
        print("*" * 65, flush=True)
        print(f"\n  👉 LIVE PUBLIC URL:  {public_url}", flush=True)
        print(f"  👉 LOCALHOST URL:    http://localhost:{PORT}", flush=True)
        print("\n  ✅ Zero Signup • Fast Global Cloudflare CDN • HTTPS Secure", flush=True)
        print("  Open this link on your phone, tablet, or share with anyone!", flush=True)
        print("  (Keep this terminal window open to keep the link active)", flush=True)
        print("*" * 65 + "\n", flush=True)
    else:
        print("\n[WARNING] Cloudflare tunnel started, waiting for connection...", flush=True)

    try:
        process.wait()
    except KeyboardInterrupt:
        print("\n[INFO] Stopping live tunnel and server...")
        process.terminate()
        sys.exit(0)


if __name__ == "__main__":
    start_live()
