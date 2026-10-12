import http.server
import os
import subprocess
import threading
import time

def run_server(port, root):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=root, **kwargs)
        def log_message(self, format, *args):
            pass # Silent

    server = http.server.HTTPServer(("127.0.0.1", port), Handler)
    server.serve_forever()

def take_screenshot(edge_path, url, width, height, output_img):
    cmd = [
        edge_path,
        "--headless",
        "--disable-gpu",
        f"--window-size={width},{height}",
        f"--screenshot={output_img}",
        url
    ]
    subprocess.run(cmd, capture_output=True, timeout=30)

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 8092

    t = threading.Thread(target=run_server, args=(port, root), daemon=True)
    t.start()
    time.sleep(1)

    url = f"http://127.0.0.1:{port}/index.html"
    ss_360 = os.path.join(root, "screenshot_360.png")
    ss_1280 = os.path.join(root, "screenshot_1280.png")

    print(f"Taking screenshot at 360x1200 -> {ss_360}")
    take_screenshot(edge_path, url, 360, 1200, ss_360)

    print(f"Taking screenshot at 1280x1000 -> {ss_1280}")
    take_screenshot(edge_path, url, 1280, 1000, ss_1280)

    print(f"360px screenshot generated: {os.path.exists(ss_360)}")
    print(f"1280px screenshot generated: {os.path.exists(ss_1280)}")

if __name__ == "__main__":
    main()
