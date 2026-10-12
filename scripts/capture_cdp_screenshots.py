import base64
import http.server
import json
import os
import socket
import subprocess
import threading
import time
import urllib.request

def ws_connect(host, port, path):
    s = socket.socket()
    s.connect((host, port))
    key = base64.b64encode(os.urandom(16)).decode()
    req = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n\r\n"
    )
    s.sendall(req.encode())
    resp = b""
    while b"\r\n\r\n" not in resp:
        resp += s.recv(4096)
    return s

def ws_send(s, text):
    payload = text.encode("utf-8")
    l = len(payload)
    mask = os.urandom(4)
    masked = bytes([b ^ mask[i % 4] for i, b in enumerate(payload)])
    if l < 126:
        header = bytes([0x81, 0x80 | l]) + mask
    elif l < 65536:
        header = bytes([0x81, 0xFE, (l >> 8) & 0xFF, l & 0xFF]) + mask
    else:
        header = bytes([0x81, 0xFF]) + l.to_bytes(8, "big") + mask
    s.sendall(header + masked)

def ws_recv(s):
    header = s.recv(2)
    b1, b2 = header[0], header[1]
    payload_len = b2 & 0x7F
    if payload_len == 126:
        payload_len = int.from_bytes(s.recv(2), "big")
    elif payload_len == 127:
        payload_len = int.from_bytes(s.recv(8), "big")
    data = b""
    while len(data) < payload_len:
        data += s.recv(min(65536, payload_len - len(data)))
    return data.decode("utf-8")

def cdp_call(s, method, params=None, msg_id=[1]):
    mid = msg_id[0]
    msg_id[0] += 1
    req = {"id": mid, "method": method, "params": params or {}}
    ws_send(s, json.dumps(req))
    while True:
        resp_text = ws_recv(s)
        resp = json.loads(resp_text)
        if resp.get("id") == mid:
            return resp.get("result", {})

def run_server(port, root):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=root, **kwargs)
        def log_message(self, format, *args):
            pass
    server = http.server.HTTPServer(("127.0.0.1", port), Handler)
    server.serve_forever()

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    server_port = 8110
    t = threading.Thread(target=run_server, args=(server_port, root), daemon=True)
    t.start()
    time.sleep(1)

    # Free port for CDP
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    cdp_port = sock.getsockname()[1]
    sock.close()

    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    proc = subprocess.Popen([
        edge_path,
        "--headless=new",
        "--disable-gpu",
        f"--remote-debugging-port={cdp_port}",
        "--remote-allow-origins=*",
        "about:blank"
    ])
    time.sleep(2)

    try:
        tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{cdp_port}/json").read())
        ws_url = tabs[0]["webSocketDebuggerUrl"]
        # Parse ws path
        path = "/" + ws_url.split("/", 3)[3]
        ws = ws_connect("127.0.0.1", cdp_port, path)

        cdp_call(ws, "Page.enable")

        url = f"http://127.0.0.1:{server_port}/index.html"
        cdp_call(ws, "Page.navigate", {"url": url})
        time.sleep(2) # Allow DOM & manifest to render

        for width, label in [(360, "360"), (1280, "1280")]:
            cdp_call(ws, "Emulation.setDeviceMetricsOverride", {
                "width": width,
                "height": 900,
                "deviceScaleFactor": 1,
                "mobile": (width == 360)
            })
            time.sleep(0.5)

            # Evaluate scroll metrics
            res = cdp_call(ws, "Runtime.evaluate", {
                "expression": "JSON.stringify({innerWidth: window.innerWidth, scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth})"
            })
            metrics = json.loads(res.get("result", {}).get("value", "{}"))
            print(f"Viewport {label}px metrics: {metrics}")
            has_hscroll = metrics.get("scrollWidth", 0) > metrics.get("clientWidth", 0)
            print(f"[{label}px] Horizontal scroll present: {has_hscroll}")

            # Capture screenshot
            ss_res = cdp_call(ws, "Page.captureScreenshot", {"format": "png"})
            img_bytes = base64.b64decode(ss_res["data"])
            out_path = os.path.join(root, f"screenshot_{label}.png")
            with open(out_path, "wb") as f:
                f.write(img_bytes)
            print(f"Saved {out_path} ({len(img_bytes):,} bytes)")

    finally:
        proc.terminate()

if __name__ == "__main__":
    main()
